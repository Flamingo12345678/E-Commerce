"""
Services de facturation optimisés utilisant les systèmes natifs
de Stripe et PayPal
"""

import os
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
                    customer = self.stripe.Customer.retrieve(shopper.stripe_customer_id)
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
                    "user_id": str(shopper.id),
                    "username": shopper.username,
                    "created_via": "django_invoice_system",
                },
            )

            # Sauvegarder l'ID
            shopper.stripe_customer_id = customer.id
            shopper.save(update_fields=["stripe_customer_id"])

            logger.info(f"Client Stripe créé: {customer.id} pour {shopper.email}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création client: {e}")
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
                collection_method="send_invoice",
                days_until_due=30,  # Par défaut 30 jours
                due_date=due_date,
                currency=invoice.currency.lower(),
                description=f"Facture #{invoice.invoice_number}",
                footer=invoice.notes or "",
                metadata={
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "django_invoice": "true",
                },
                # Activer le calcul automatique des taxes
                automatic_tax={"enabled": True},
                # Permettre les paiements par carte
                default_payment_method=None,
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
                        "item_id": str(item.id),
                        "unit_price": str(item.unit_price),
                    },
                )

            # Finaliser la facture pour qu'elle soit prête à être envoyée
            stripe_invoice = self.stripe.Invoice.finalize_invoice(stripe_invoice.id)

            # Mettre à jour notre modèle local
            invoice.provider_invoice_id = stripe_invoice.id
            invoice.provider_url = stripe_invoice.hosted_invoice_url
            invoice.provider_pdf_url = stripe_invoice.invoice_pdf
            invoice.save(
                update_fields=[
                    "provider_invoice_id",
                    "provider_url",
                    "provider_pdf_url",
                ]
            )

            logger.info(f"Facture Stripe native créée: {stripe_invoice.id}")

            return {
                "success": True,
                "stripe_invoice_id": stripe_invoice.id,
                "status": stripe_invoice.status,
                "hosted_url": stripe_invoice.hosted_invoice_url,
                "pdf_url": stripe_invoice.invoice_pdf,
                "total": stripe_invoice.total / 100,
                "amount_due": stripe_invoice.amount_due / 100,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erreur création facture Stripe: {e}")
            return {"success": False, "error": str(e), "error_type": type(e).__name__}

    def send_stripe_invoice(self, invoice: Invoice) -> dict:
        """
        Envoie la facture Stripe par email au client
        """
        try:
            if not invoice.provider_invoice_id:
                raise InvoiceServiceError("Aucun ID de facture Stripe trouvé")

            # Envoyer la facture
            sent_invoice = self.stripe.Invoice.send_invoice(invoice.provider_invoice_id)

            # Mettre à jour le statut local
            invoice.status = "sent"
            invoice.sent_at = timezone.now()
            invoice.save(update_fields=["status", "sent_at"])

            logger.info(f"Facture Stripe envoyée: {sent_invoice.id}")

            return {
                "success": True,
                "status": sent_invoice.status,
                "sent_at": timezone.now(),
                "hosted_url": sent_invoice.hosted_invoice_url,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erreur envoi facture Stripe: {e}")
            return {"success": False, "error": str(e)}

    def sync_invoice_status(self, invoice: Invoice) -> dict:
        """
        Synchronise le statut de la facture avec Stripe
        """
        try:
            if not invoice.provider_invoice_id:
                return {"success": False, "error": "Pas d ID Stripe"}

            # Récupérer la facture depuis Stripe
            stripe_invoice = self.stripe.Invoice.retrieve(invoice.provider_invoice_id)

            # Mapper les statuts Stripe
            status_mapping = {
                "draft": "draft",
                "open": "sent",
                "paid": "paid",
                "uncollectible": "overdue",
                "void": "cancelled",
            }

            new_status = status_mapping.get(stripe_invoice.status, "unknown")

            # Mettre à jour si nécessaire
            if invoice.status != new_status:
                invoice.status = new_status
                invoice.save(update_fields=["status"])

                # Si payée, créer un enregistrement de paiement
                if new_status == "paid" and stripe_invoice.paid:
                    self._create_payment_record(invoice, stripe_invoice)

            return {
                "success": True,
                "status": new_status,
                "stripe_status": stripe_invoice.status,
                "amount_paid": stripe_invoice.amount_paid / 100,
                "amount_due": stripe_invoice.amount_due / 100,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erreur sync statut Stripe: {e}")
            return {"success": False, "error": str(e)}

    def _create_payment_record(self, invoice: Invoice, stripe_invoice):
        """
        Crée un enregistrement de paiement local
        """
        try:
            # Éviter les doublons
            if InvoicePayment.objects.filter(
                invoice=invoice, provider_payment_id=stripe_invoice.payment_intent
            ).exists():
                return

            InvoicePayment.objects.create(
                invoice=invoice,
                amount=Decimal(str(stripe_invoice.amount_paid / 100)),
                currency=stripe_invoice.currency.upper(),
                provider="stripe",
                provider_payment_id=(
                    stripe_invoice.payment_intent or stripe_invoice.id
                ),
                status="completed",
                paid_at=timezone.now(),
                metadata={
                    "stripe_invoice_id": stripe_invoice.id,
                    "payment_method": getattr(
                        stripe_invoice, "default_payment_method", None
                    ),
                },
            )

            logger.info(f"Enregistrement de paiement créé pour la facture {invoice.id}")

        except Exception as e:
            logger.error(f"Erreur création enregistrement paiement: {e}")


class PayPalNativeInvoiceService:
    """
    Service utilisant le système de facturation natif de PayPal
    https://developer.paypal.com/docs/invoicing/
    """

    def __init__(self):
        try:
            from paypalcheckoutsdk.core import (
                SandBoxEnvironment,
                LiveEnvironment,
                PayPalHttpClient,
            )

            # Configuration de l'environnement
            if getattr(settings, "PAYPAL_MODE", "sandbox") == "live":
                environment = LiveEnvironment(
                    client_id=settings.PAYPAL_CLIENT_ID,
                    client_secret=settings.PAYPAL_CLIENT_SECRET,
                )
            else:
                environment = SandBoxEnvironment(
                    client_id=settings.PAYPAL_CLIENT_ID,
                    client_secret=settings.PAYPAL_CLIENT_SECRET,
                )

            self.client = PayPalHttpClient(environment)
        except ImportError:
            logger.warning("SDK PayPal non installé")
            self.client = None

    def create_paypal_invoice(self, invoice: Invoice) -> dict:
        """
        Crée une facture native PayPal
        """
        if not self.client:
            return {"success": False, "error": "SDK PayPal non disponible"}

        try:
            from paypalcheckoutsdk.invoices import InvoicesCreateRequest

            # Préparer les données de la facture
            invoice_data = {
                "detail": {
                    "invoice_number": invoice.invoice_number,
                    "currency_code": invoice.currency.upper(),
                    "invoice_date": invoice.created_at.strftime("%Y-%m-%d"),
                    "note": invoice.notes or "",
                },
                "invoicer": {
                    "business_name": getattr(
                        settings, "COMPANY_NAME", "Mon Entreprise"
                    ),
                    "email_address": getattr(
                        settings,
                        "COMPANY_EMAIL",
                        os.environ.get("COMPANY_EMAIL", "noreply@example.com"),
                    ),
                },
                "primary_recipients": [
                    {
                        "billing_info": {
                            "email_address": invoice.customer.email,
                            "name": {
                                "given_name": invoice.customer.first_name,
                                "surname": invoice.customer.last_name,
                            },
                        }
                    }
                ],
                "items": [],
                "configuration": {
                    "allow_tip": False,
                    "tax_calculated_after_discount": True,
                    "tax_inclusive": False,
                },
            }

            # Ajouter les articles
            for item in invoice.items.all():
                invoice_data["items"].append(
                    {
                        "name": item.description,
                        "description": item.description,
                        "quantity": str(int(item.quantity)),
                        "unit_amount": {
                            "currency_code": invoice.currency.upper(),
                            "value": str(item.unit_price),
                        },
                    }
                )

            # Créer la requête
            request = InvoicesCreateRequest()
            request.request_body(invoice_data)

            # Exécuter la requête
            response = self.client.execute(request)

            if response.status_code == 201:
                paypal_invoice = response.result

                # Mettre à jour notre modèle
                invoice.provider_invoice_id = paypal_invoice.id
                invoice.provider_url = paypal_invoice.href
                invoice.save(update_fields=["provider_invoice_id", "provider_url"])

                logger.info(f"Facture PayPal créée: {paypal_invoice.id}")

                return {
                    "success": True,
                    "paypal_invoice_id": paypal_invoice.id,
                    "status": paypal_invoice.status,
                    "href": paypal_invoice.href,
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}",
                }

        except Exception as e:
            logger.error(f"Erreur création facture PayPal: {e}")
            return {"success": False, "error": str(e)}

    def send_paypal_invoice(self, invoice: Invoice) -> dict:
        """
        Envoie la facture PayPal par email
        """
        if not self.client:
            return {"success": False, "error": "SDK PayPal non disponible"}

        try:
            from paypalcheckoutsdk.invoices import InvoicesSendRequest

            if not invoice.provider_invoice_id:
                raise InvoiceServiceError("Aucun ID de facture PayPal trouvé")

            # Créer la requête d'envoi
            request = InvoicesSendRequest(invoice.provider_invoice_id)
            request.request_body(
                {
                    "send_to_invoicer": True,
                    "send_to_recipient": True,
                }
            )

            # Exécuter la requête
            response = self.client.execute(request)

            if response.status_code == 202:
                # Mettre à jour le statut local
                invoice.status = "sent"
                invoice.sent_at = timezone.now()
                invoice.save(update_fields=["status", "sent_at"])

                logger.info(f"Facture PayPal envoyée: {invoice.provider_invoice_id}")

                return {
                    "success": True,
                    "sent_at": timezone.now(),
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}",
                }

        except Exception as e:
            logger.error(f"Erreur envoi facture PayPal: {e}")
            return {"success": False, "error": str(e)}


class UnifiedInvoiceManager:
    """
    Gestionnaire unifié pour les factures Stripe et PayPal natifs
    """

    def __init__(self):
        self.stripe_service = StripeNativeInvoiceService()
        self.paypal_service = PayPalNativeInvoiceService()

    def create_invoice(self, invoice: Invoice, provider: str = "stripe") -> dict:
        """
        Crée une facture avec le fournisseur spécifié
        """
        invoice.provider = provider
        invoice.save(update_fields=["provider"])

        if provider == "stripe":
            return self.stripe_service.create_native_invoice(invoice)
        elif provider == "paypal":
            return self.paypal_service.create_paypal_invoice(invoice)
        else:
            return {"success": False, "error": f"Fournisseur non supporté: {provider}"}

    def send_invoice(self, invoice: Invoice) -> dict:
        """
        Envoie une facture selon son fournisseur
        """
        if invoice.provider == "stripe":
            return self.stripe_service.send_stripe_invoice(invoice)
        elif invoice.provider == "paypal":
            return self.paypal_service.send_paypal_invoice(invoice)
        else:
            return {
                "success": False,
                "error": f"Fournisseur non supporté: {invoice.provider}",
            }

    def sync_all_invoices(self):
        """
        Synchronise toutes les factures avec leurs fournisseurs
        """
        for invoice in Invoice.objects.filter(
            provider_invoice_id__isnull=False, status__in=["sent", "overdue"]
        ):
            if invoice.provider == "stripe":
                self.stripe_service.sync_invoice_status(invoice)
            # PayPal sync à implémenter si nécessaire


# Rétrocompatibilité avec l'ancienne interface
class InvoiceManager(UnifiedInvoiceManager):
    """Alias pour la rétrocompatibilité"""

    pass


class StripeInvoiceService(StripeNativeInvoiceService):
    """Alias pour la rétrocompatibilité"""

    pass
