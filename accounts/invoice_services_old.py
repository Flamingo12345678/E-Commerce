
"""
Services de facturation optimisés utilisant les systèmes natifs de Stripe et PayPal
"""

import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Shopper, Invoice, InvoiceItem, InvoicePayment

logger = logging.getLogger(__name__)


class InvoiceServiceError(Exception):
    """Exception pour les erreurs de service de facturation"""
    pass


class StripeNativeInvoiceService:
    """
    Service utilisant le système de facturation natif de Stripe
    https://stripe.com/docs/invoicing
    """

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.stripe = stripe

    def ensure_customer(self, shopper: Shopper) -> str:
        """
        Assure qu'un client Stripe existe pour ce shopper
        """
        try:
            if shopper.stripe_customer_id:
                # Vérifier que le client existe toujours
                try:
                    customer = self.stripe.Customer.retrieve(
                        shopper.stripe_customer_id
                    )
                    return customer.id
                except stripe.error.InvalidRequestError:
                    # Client n'existe plus, en créer un nouveau
                    shopper.stripe_customer_id = None

            # Créer un nouveau client Stripe
            full_name = f"{shopper.first_name} {shopper.last_name}".strip()
            customer = self.stripe.Customer.create(
                email=shopper.email,
                name=full_name or shopper.username,
                phone=shopper.phone_number or None,
                metadata={
                    'user_id': str(shopper.id),
                    'username': shopper.username,
                    'created_via': 'django_invoice_system'
                }
            )

            # Sauvegarder l'ID
            shopper.stripe_customer_id = customer.id
            shopper.save(update_fields=['stripe_customer_id'])

            logger.info(f"Client Stripe créé: {customer.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe création client: {e}")
            raise InvoiceServiceError(f"Erreur Stripe: {str(e)}")

    def create_native_invoice(self, invoice: Invoice) -> dict:
        """
        Crée une facture native Stripe avec tous les éléments
        """
        try:
            # Assurer que le client existe
            customer_id = self.ensure_customer(invoice.customer)

            # Calculer la date d'échéance
            due_date = None
            if invoice.due_date:
                due_date = int(invoice.due_date.timestamp())

            # Créer la facture Stripe
            stripe_invoice = self.stripe.Invoice.create(
                customer=customer_id,
                collection_method='send_invoice',
                days_until_due=30,  # Par défaut 30 jours
                due_date=due_date,
                currency=invoice.currency.lower(),
                description=f"Facture #{invoice.invoice_number}",
                footer=invoice.notes or "",
                metadata={
                    'invoice_id': str(invoice.id),
                    'invoice_number': invoice.invoice_number,
                    'django_invoice': 'true'
                },
                # Activer le calcul automatique des taxes
                automatic_tax={'enabled': True},
            )

            # Ajouter chaque ligne de facture
            for item in invoice.items.all():
                self.stripe.InvoiceItem.create(
                    customer=customer_id,
                    invoice=stripe_invoice.id,
                    amount=int(item.line_total * 100),  # Centimes
                    currency=invoice.currency.lower(),
                    description=item.description,
                    quantity=int(item.quantity),
                    metadata={
                        'item_id': str(item.id),
                        'unit_price': str(item.unit_price)
                    }
                )

            # Finaliser la facture
            finalized_invoice = self.stripe.Invoice.finalize_invoice(
                stripe_invoice.id
            )

            # Mettre à jour notre modèle local
            invoice.provider_invoice_id = finalized_invoice.id
            invoice.provider_url = finalized_invoice.hosted_invoice_url
            invoice.provider_pdf_url = finalized_invoice.invoice_pdf
            invoice.save(update_fields=[
                'provider_invoice_id', 'provider_url', 'provider_pdf_url'
            ])

            logger.info(f"Facture Stripe native créée: {finalized_invoice.id}")
            
            return {
                'success': True,
                'stripe_invoice_id': finalized_invoice.id,
                'status': finalized_invoice.status,
                'hosted_url': finalized_invoice.hosted_invoice_url,
                'pdf_url': finalized_invoice.invoice_pdf,
                'total': finalized_invoice.total / 100,
                'amount_due': finalized_invoice.amount_due / 100,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erreur création facture Stripe: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    def send_stripe_invoice(self, invoice: Invoice) -> dict:
        """
        Envoie la facture Stripe par email au client
        """
        try:
            if not invoice.provider_invoice_id:
                raise InvoiceServiceError("Aucun ID de facture Stripe trouvé")

            # Envoyer la facture
            sent_invoice = self.stripe.Invoice.send_invoice(
                invoice.provider_invoice_id
            )

            # Mettre à jour le statut local
            invoice.status = 'sent'
            invoice.sent_at = timezone.now()
            invoice.save(update_fields=['status', 'sent_at'])

            logger.info(f"Facture Stripe envoyée: {sent_invoice.id}")
            
            return {
                'success': True,
                'status': sent_invoice.status,
                'sent_at': timezone.now(),
                'hosted_url': sent_invoice.hosted_invoice_url,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erreur envoi facture Stripe: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def sync_invoice_status(self, invoice: Invoice) -> dict:
        """
        Synchronise le statut de la facture avec Stripe
        """
        try:
            if not invoice.provider_invoice_id:
                return {'success': False, 'error': 'Pas d ID Stripe'}

            # Récupérer la facture depuis Stripe
            stripe_invoice = self.stripe.Invoice.retrieve(
                invoice.provider_invoice_id
            )

            # Mapper les statuts Stripe
            status_mapping = {
                'draft': 'draft',
                'open': 'sent',
                'paid': 'paid',
                'uncollectible': 'overdue',
                'void': 'cancelled'
            }

            new_status = status_mapping.get(stripe_invoice.status, 'unknown')
            
            # Mettre à jour si nécessaire
            if invoice.status != new_status:
                invoice.status = new_status
                invoice.save(update_fields=['status'])

                # Si payée, créer un enregistrement de paiement
                if new_status == 'paid' and stripe_invoice.paid:
                    self._create_payment_record(invoice, stripe_invoice)

            return {
                'success': True,
                'status': new_status,
                'stripe_status': stripe_invoice.status,
                'amount_paid': stripe_invoice.amount_paid / 100,
                'amount_due': stripe_invoice.amount_due / 100,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erreur sync statut Stripe: {e}")
            return {'success': False, 'error': str(e)}

    def _create_payment_record(self, invoice: Invoice, stripe_invoice):
        """
        Crée un enregistrement de paiement local
        """
        try:
            # Éviter les doublons
            payment_id = stripe_invoice.payment_intent or stripe_invoice.id
            if InvoicePayment.objects.filter(
                invoice=invoice,
                provider_payment_id=payment_id
            ).exists():
                return

            InvoicePayment.objects.create(
                invoice=invoice,
                amount=Decimal(str(stripe_invoice.amount_paid / 100)),
                currency=stripe_invoice.currency.upper(),
                provider='stripe',
                provider_payment_id=payment_id,
                status='completed',
                paid_at=timezone.now(),
                metadata={
                    'stripe_invoice_id': stripe_invoice.id,
                }
            )

            logger.info(f"Paiement créé pour facture {invoice.id}")

        except Exception as e:
            logger.error(f"Erreur création paiement: {e}")


class UnifiedInvoiceManager:
    """
    Gestionnaire unifié pour les factures Stripe et PayPal natifs
    """

    def __init__(self):
        self.stripe_service = StripeNativeInvoiceService()

    def create_invoice(self, invoice: Invoice, provider: str = 'stripe') -> dict:
        """
        Crée une facture avec le fournisseur spécifié
        """
        invoice.provider = provider
        invoice.save(update_fields=['provider'])

        if provider == 'stripe':
            return self.stripe_service.create_native_invoice(invoice)
        else:
            return {
                'success': False,
                'error': f'Fournisseur non supporté: {provider}'
            }

    def send_invoice(self, invoice: Invoice) -> dict:
        """
        Envoie une facture selon son fournisseur
        """
        if invoice.provider == 'stripe':
            return self.stripe_service.send_stripe_invoice(invoice)
        else:
            return {
                'success': False,
                'error': f'Fournisseur non supporté: {invoice.provider}'
            }

    def sync_all_invoices(self):
        """
        Synchronise toutes les factures avec leurs fournisseurs
        """
        for invoice in Invoice.objects.filter(
            provider_invoice_id__isnull=False,
            status__in=['sent', 'overdue']
        ):
            if invoice.provider == 'stripe':
                self.stripe_service.sync_invoice_status(invoice)


# Rétrocompatibilité avec l'ancienne interface
class InvoiceManager(UnifiedInvoiceManager):
    """Alias pour la rétrocompatibilité"""
    pass


class StripeInvoiceService(StripeNativeInvoiceService):
    """Alias pour la rétrocompatibilité"""
    pass


import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Shopper, Invoice, InvoiceItem, InvoicePayment

import stripe
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, Any, Optional
import requests
import json

# Configuration du logging
logger = logging.getLogger('payment')

# Configuration Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeInvoiceService:
    """
    Service pour gérer les factures Stripe
    """
    
    def __init__(self):
        self.stripe = stripe
    
    def create_customer(self, user) -> str:
        """
        Crée un client Stripe ou récupère l'ID existant
        """
        try:
            # Vérifier si le client existe déjà
            if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
                try:
                    customer = self.stripe.Customer.retrieve(user.stripe_customer_id)
                    return customer.id
                except stripe.error.InvalidRequestError:
                    # Le client n'existe plus côté Stripe
                    pass
            
            # Créer un nouveau client
            customer = self.stripe.Customer.create(
                email=user.email,
                name=user.get_full_name(),
                phone=getattr(user, 'phone_number', ''),
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )
            
            # Sauvegarder l'ID client (nécessite d'ajouter ce champ au modèle User)
            if not hasattr(user, 'stripe_customer_id'):
                from django.db import migrations, models
                # TODO: Ajouter une migration pour ce champ
                pass
            
            logger.info(f"Client Stripe créé: {customer.id} pour l'utilisateur {user.id}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du client Stripe: {e}")
            raise
    
    def create_invoice(self, invoice_model) -> str:
        """
        Crée une facture Stripe basée sur notre modèle
        """
        try:
            # Créer ou récupérer le client
            customer_id = self.create_customer(invoice_model.customer)
            
            # Créer la facture Stripe
            stripe_invoice = self.stripe.Invoice.create(
                customer=customer_id,
                collection_method='send_invoice',
                days_until_due=max(1, invoice_model.days_until_due),
                currency=invoice_model.currency.lower(),
                description=f"Facture {invoice_model.invoice_number}",
                metadata={
                    'invoice_id': str(invoice_model.id),
                    'invoice_number': invoice_model.invoice_number,
                }
            )
            
            # Ajouter les lignes de facture
            for item in invoice_model.items.all():
                self.stripe.InvoiceItem.create(
                    customer=customer_id,
                    invoice=stripe_invoice.id,
                    amount=int(item.line_total * 100),  # Stripe utilise les centimes
                    currency=invoice_model.currency.lower(),
                    description=item.description,
                    quantity=int(item.quantity),
                )
            
            # Finaliser la facture
            stripe_invoice = self.stripe.Invoice.finalize_invoice(stripe_invoice.id)
            
            # Sauvegarder l'ID Stripe dans notre modèle
            invoice_model.stripe_invoice_id = stripe_invoice.id
            invoice_model.save()
            
            logger.info(f"Facture Stripe créée: {stripe_invoice.id}")
            return stripe_invoice.id
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la facture Stripe: {e}")
            raise
    
    def send_invoice(self, invoice_model) -> bool:
        """
        Envoie une facture Stripe par email
        """
        try:
            if not invoice_model.stripe_invoice_id:
                raise ValueError("La facture n'a pas d'ID Stripe")
            
            # Envoyer la facture
            sent_invoice = self.stripe.Invoice.send_invoice(
                invoice_model.stripe_invoice_id
            )
            
            # Mettre à jour notre modèle
            invoice_model.send_invoice()
            
            logger.info(f"Facture Stripe envoyée: {sent_invoice.id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la facture Stripe: {e}")
            return False
    
    def get_invoice_status(self, stripe_invoice_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une facture Stripe
        """
        try:
            invoice = self.stripe.Invoice.retrieve(stripe_invoice_id)
            return {
                'status': invoice.status,
                'paid': invoice.paid,
                'amount_paid': Decimal(invoice.amount_paid / 100),
                'amount_due': Decimal(invoice.amount_due / 100),
                'payment_intent': invoice.payment_intent,
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {}
    
    def create_payment_link(self, invoice_model) -> Optional[str]:
        """
        Crée un lien de paiement pour une facture
        """
        try:
            if not invoice_model.stripe_invoice_id:
                self.create_invoice(invoice_model)
            
            invoice = self.stripe.Invoice.retrieve(invoice_model.stripe_invoice_id)
            return invoice.hosted_invoice_url
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du lien de paiement: {e}")
            return None


class PayPalInvoiceService:
    """
    Service pour gérer les factures PayPal
    """
    
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.mode = settings.PAYPAL_MODE
        self.base_url = (
            "https://api-m.sandbox.paypal.com" 
            if self.mode == "sandbox" 
            else "https://api-m.paypal.com"
        )
        self.access_token = None
    
    def get_access_token(self) -> str:
        """
        Obtient un token d'accès PayPal
        """
        try:
            if self.access_token:
                return self.access_token
            
            url = f"{self.base_url}/v1/oauth2/token"
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            data = 'grant_type=client_credentials'
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                return self.access_token
            else:
                raise Exception(f"Erreur PayPal OAuth: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token PayPal: {e}")
            raise
    
    def create_invoice(self, invoice_model) -> str:
        """
        Crée une facture PayPal
        """
        try:
            token = self.get_access_token()
            
            url = f"{self.base_url}/v2/invoicing/invoices"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            }
            
            # Préparer les données de la facture
            invoice_data = {
                "detail": {
                    "invoice_number": invoice_model.invoice_number,
                    "reference": f"REF-{invoice_model.id}",
                    "invoice_date": invoice_model.issue_date.isoformat(),
                    "currency_code": invoice_model.currency,
                    "note": invoice_model.notes,
                    "term": invoice_model.template.payment_terms if invoice_model.template else "",
                    "memo": f"Facture émise par {settings.ADMIN_SITE_HEADER}",
                },
                "invoicer": {
                    "name": {
                        "given_name": "Équipe",
                        "surname": "YEE E-Commerce"
                    },
                    "address": {
                        "address_line_1": "123 Rue du Commerce",
                        "admin_area_2": "Paris",
                        "postal_code": "75001",
                        "country_code": "FR"
                    },
                    "email_address": settings.EMAIL_HOST_USER or "admin@example.com",
                },
                "primary_recipients": [
                    {
                        "billing_info": {
                            "name": {
                                "given_name": invoice_model.customer.first_name,
                                "surname": invoice_model.customer.last_name
                            },
                            "email_address": invoice_model.customer.email,
                        }
                    }
                ],
                "items": [
                    {
                        "name": item.description,
                        "description": item.description,
                        "quantity": str(int(item.quantity)),
                        "unit_amount": {
                            "currency_code": invoice_model.currency,
                            "value": str(item.unit_price)
                        },
                        "unit_of_measure": "QUANTITY"
                    }
                    for item in invoice_model.items.all()
                ],
                "configuration": {
                    "partial_payment": {
                        "allow_partial_payment": False
                    },
                    "allow_tip": False,
                    "tax_calculated_after_discount": True,
                    "tax_inclusive": False
                },
                "amount": {
                    "breakdown": {
                        "item_total": {
                            "currency_code": invoice_model.currency,
                            "value": str(invoice_model.subtotal)
                        },
                        "tax_total": {
                            "currency_code": invoice_model.currency,
                            "value": str(invoice_model.tax_amount)
                        },
                        "discount": {
                            "currency_code": invoice_model.currency,
                            "value": str(invoice_model.discount_amount)
                        }
                    }
                }
            }
            
            response = requests.post(url, headers=headers, json=invoice_data)
            
            if response.status_code == 201:
                invoice_response = response.json()
                paypal_invoice_id = invoice_response['id']
                
                # Sauvegarder l'ID PayPal
                invoice_model.paypal_invoice_id = paypal_invoice_id
                invoice_model.save()
                
                logger.info(f"Facture PayPal créée: {paypal_invoice_id}")
                return paypal_invoice_id
            else:
                raise Exception(f"Erreur création facture PayPal: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la facture PayPal: {e}")
            raise
    
    def send_invoice(self, invoice_model) -> bool:
        """
        Envoie une facture PayPal
        """
        try:
            if not invoice_model.paypal_invoice_id:
                raise ValueError("La facture n'a pas d'ID PayPal")
            
            token = self.get_access_token()
            
            url = f"{self.base_url}/v2/invoicing/invoices/{invoice_model.paypal_invoice_id}/send"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            }
            
            send_data = {
                "send_to_recipient": True,
                "send_to_invoicer": True
            }
            
            response = requests.post(url, headers=headers, json=send_data)
            
            if response.status_code == 202:
                # Mettre à jour notre modèle
                invoice_model.send_invoice()
                
                logger.info(f"Facture PayPal envoyée: {invoice_model.paypal_invoice_id}")
                return True
            else:
                raise Exception(f"Erreur envoi facture PayPal: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la facture PayPal: {e}")
            return False
    
    def get_invoice_status(self, paypal_invoice_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une facture PayPal
        """
        try:
            token = self.get_access_token()
            
            url = f"{self.base_url}/v2/invoicing/invoices/{paypal_invoice_id}"
            headers = {
                'Authorization': f'Bearer {token}',
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                invoice_data = response.json()
                return {
                    'status': invoice_data.get('status'),
                    'paid': invoice_data.get('status') == 'PAID',
                    'amount_paid': Decimal(
                        invoice_data.get('payments', {}).get('paid_amount', {}).get('value', '0')
                    ),
                    'amount_due': Decimal(
                        invoice_data.get('amount', {}).get('value', '0')
                    ),
                }
            else:
                raise Exception(f"Erreur récupération statut PayPal: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut PayPal: {e}")
            return {}
    
    def create_payment_link(self, invoice_model) -> Optional[str]:
        """
        Crée un lien de paiement pour une facture PayPal
        """
        try:
            if not invoice_model.paypal_invoice_id:
                self.create_invoice(invoice_model)
            
            # PayPal génère automatiquement un lien lors de l'envoi
            # Nous pouvons récupérer l'URL depuis les détails de la facture
            status_data = self.get_invoice_status(invoice_model.paypal_invoice_id)
            
            # Cette URL est généralement disponible dans les liens de la facture
            token = self.get_access_token()
            url = f"{self.base_url}/v2/invoicing/invoices/{invoice_model.paypal_invoice_id}"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                invoice_data = response.json()
                links = invoice_data.get('links', [])
                
                for link in links:
                    if link.get('rel') == 'payer-view':
                        return link.get('href')
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du lien de paiement PayPal: {e}")
            return None


class InvoiceManager:
    """
    Gestionnaire principal pour les factures
    Coordonne les services Stripe et PayPal
    """
    
    def __init__(self):
        self.stripe_service = StripeInvoiceService()
        self.paypal_service = PayPalInvoiceService()
    
    def create_invoice_with_provider(self, invoice_model, provider: str) -> bool:
        """
        Crée une facture avec le fournisseur spécifié
        """
        try:
            if provider == 'stripe':
                self.stripe_service.create_invoice(invoice_model)
            elif provider == 'paypal':
                self.paypal_service.create_invoice(invoice_model)
            else:
                raise ValueError(f"Fournisseur non supporté: {provider}")
            
            logger.info(f"Facture créée avec {provider}: {invoice_model.invoice_number}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la facture: {e}")
            return False
    
    def send_invoice_with_provider(self, invoice_model, provider: str) -> bool:
        """
        Envoie une facture avec le fournisseur spécifié
        """
        try:
            if provider == 'stripe':
                return self.stripe_service.send_invoice(invoice_model)
            elif provider == 'paypal':
                return self.paypal_service.send_invoice(invoice_model)
            else:
                raise ValueError(f"Fournisseur non supporté: {provider}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la facture: {e}")
            return False
    
    def sync_invoice_status(self, invoice_model) -> bool:
        """
        Synchronise le statut d'une facture avec les fournisseurs
        """
        try:
            updated = False
            
            # Vérifier Stripe
            if invoice_model.stripe_invoice_id:
                stripe_status = self.stripe_service.get_invoice_status(
                    invoice_model.stripe_invoice_id
                )
                if stripe_status.get('paid'):
                    invoice_model.mark_as_paid(payment_method='stripe')
                    updated = True
            
            # Vérifier PayPal
            if invoice_model.paypal_invoice_id:
                paypal_status = self.paypal_service.get_invoice_status(
                    invoice_model.paypal_invoice_id
                )
                if paypal_status.get('paid'):
                    invoice_model.mark_as_paid(payment_method='paypal')
                    updated = True
            
            return updated
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {e}")
            return False


# Rétrocompatibilité avec l'ancienne interface
class InvoiceManager(UnifiedInvoiceManager):
    """Alias pour la rétrocompatibilité"""
    pass


class StripeInvoiceService(StripeNativeInvoiceService):
    """Alias pour la rétrocompatibilité"""
    pass
