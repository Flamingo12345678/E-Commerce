"""
Services de traitement des paiements pour YEE E-Commerce
Intégrations Stripe et PayPal
"""

import stripe
import paypalrestsdk
import hashlib
import logging
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import PaymentMethod, Transaction
from .utils import validate_card_number, validate_expiry_date, validate_cvv

# Configuration du logging
logger = logging.getLogger("payment")

# Configuration Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Configuration PayPal
paypalrestsdk.configure(
    {
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET,
    }
)


class PaymentProcessingError(Exception):
    """Exception personnalisée pour les erreurs de paiement"""

    pass


class StripePaymentProcessor:
    """
    Service pour traiter les paiements via Stripe
    """

    @staticmethod
    def create_payment_intent(amount, currency="EUR", description="", metadata=None):
        """
        Crée un PaymentIntent Stripe

        Args:
            amount (Decimal): Montant en centimes
            currency (str): Devise (EUR, USD, etc.)
            description (str): Description du paiement
            metadata (dict): Métadonnées additionnelles

        Returns:
            dict: PaymentIntent créé
        """
        try:
            # Convertir en centimes pour Stripe
            amount_cents = int(amount * 100)

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={
                    "enabled": True,
                },
            )

            logger.info(f"PaymentIntent créé: {payment_intent.id}")
            return payment_intent

        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            raise PaymentProcessingError(f"Erreur de création du paiement: {e}")

    @staticmethod
    def confirm_payment_intent(payment_intent_id, payment_method_id):
        """
        Confirme un PaymentIntent avec une méthode de paiement

        Args:
            payment_intent_id (str): ID du PaymentIntent
            payment_method_id (str): ID de la méthode de paiement Stripe

        Returns:
            dict: PaymentIntent confirmé
        """
        try:
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id, payment_method=payment_method_id
            )

            logger.info(f"PaymentIntent confirmé: {payment_intent_id}")
            return payment_intent

        except stripe.error.StripeError as e:
            logger.error(f"Erreur confirmation Stripe: {e}")
            raise PaymentProcessingError(f"Erreur de confirmation du paiement: {e}")

    @staticmethod
    def create_refund(payment_intent_id, amount=None, reason="requested_by_customer"):
        """
        Crée un remboursement Stripe

        Args:
            payment_intent_id (str): ID du PaymentIntent à rembourser
            amount (int): Montant en centimes (None pour remboursement total)
            reason (str): Raison du remboursement

        Returns:
            dict: Remboursement créé
        """
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "reason": reason,
            }

            if amount:
                refund_data["amount"] = int(amount * 100)

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Remboursement créé: {refund.id}")
            return refund

        except stripe.error.StripeError as e:
            logger.error(f"Erreur remboursement Stripe: {e}")
            raise PaymentProcessingError(f"Erreur de remboursement: {e}")


class PayPalPaymentProcessor:
    """
    Service pour traiter les paiements via PayPal
    """

    @staticmethod
    def create_payment(
        amount, currency="EUR", description="", return_url="", cancel_url=""
    ):
        """
        Crée un paiement PayPal

        Args:
            amount (Decimal): Montant du paiement
            currency (str): Devise
            description (str): Description du paiement
            return_url (str): URL de retour après paiement
            cancel_url (str): URL d'annulation

        Returns:
            dict: Paiement PayPal créé
        """
        try:
            payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": return_url,
                        "cancel_url": cancel_url,
                    },
                    "transactions": [
                        {
                            "amount": {"total": str(amount), "currency": currency},
                            "description": description,
                        }
                    ],
                }
            )

            if payment.create():
                logger.info(f"Paiement PayPal créé: {payment.id}")
                return payment
            else:
                error_msg = f"Erreur PayPal: {payment.error}"
                logger.error(error_msg)
                raise PaymentProcessingError(error_msg)

        except Exception as e:
            logger.error(f"Erreur création paiement PayPal: {e}")
            raise PaymentProcessingError(f"Erreur de création du paiement PayPal: {e}")

    @staticmethod
    def execute_payment(payment_id, payer_id):
        """
        Exécute un paiement PayPal après approbation

        Args:
            payment_id (str): ID du paiement PayPal
            payer_id (str): ID du payeur

        Returns:
            dict: Paiement exécuté
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)

            if payment.execute({"payer_id": payer_id}):
                logger.info(f"Paiement PayPal exécuté: {payment_id}")
                return payment
            else:
                error_msg = f"Erreur exécution PayPal: {payment.error}"
                logger.error(error_msg)
                raise PaymentProcessingError(error_msg)

        except Exception as e:
            logger.error(f"Erreur exécution paiement PayPal: {e}")
            raise PaymentProcessingError(f"Erreur d'exécution du paiement PayPal: {e}")


class PaymentMethodService:
    """
    Service pour gérer les méthodes de paiement des utilisateurs
    """

    @staticmethod
    def add_payment_method(
        user,
        card_number,
        cardholder_name,
        expiry_month,
        expiry_year,
        cvv,
        card_type="other",
    ):
        """
        Ajoute une nouvelle méthode de paiement pour un utilisateur

        Args:
            user: Instance du modèle Shopper
            card_number (str): Numéro de carte
            cardholder_name (str): Nom du porteur
            expiry_month (int): Mois d'expiration
            expiry_year (int): Année d'expiration
            cvv (str): Code CVV
            card_type (str): Type de carte

        Returns:
            PaymentMethod: Instance créée
        """
        # Validations
        if not validate_card_number(card_number):
            raise ValidationError("Numéro de carte invalide")

        if not validate_expiry_date(f"{expiry_month:02d}/{expiry_year % 100:02d}"):
            raise ValidationError("Date d'expiration invalide")

        if not validate_cvv(cvv):
            raise ValidationError("CVV invalide")

        # Hacher le numéro de carte pour le stockage sécurisé
        card_hash = hashlib.sha256(card_number.encode()).hexdigest()

        # Déterminer automatiquement le type de carte si pas spécifié
        if card_type == "other":
            card_type = PaymentMethodService._detect_card_type(card_number)

        # Créer la méthode de paiement
        payment_method = PaymentMethod.objects.create(
            user=user,
            card_type=card_type,
            card_number_hash=card_hash,
            last4=card_number[-4:],
            cardholder_name=cardholder_name,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            is_default=not user.payment_methods.exists(),  # Premier = défaut
        )

        logger.info(f"Méthode de paiement ajoutée pour {user.username}")
        return payment_method

    @staticmethod
    def _detect_card_type(card_number):
        """
        Détecte automatiquement le type de carte basé sur le numéro

        Args:
            card_number (str): Numéro de carte

        Returns:
            str: Type de carte détecté
        """
        # Supprime les espaces et caractères non numériques
        clean_number = "".join(filter(str.isdigit, card_number))

        if clean_number.startswith("4"):
            return "visa"
        elif clean_number.startswith(("51", "52", "53", "54", "55")):
            return "mastercard"
        elif clean_number.startswith(("34", "37")):
            return "amex"
        elif clean_number.startswith("6"):
            return "discover"
        else:
            return "other"


class TransactionService:
    """
    Service pour gérer les transactions de paiement
    """

    @staticmethod
    def create_transaction(
        user, amount, provider, order_id="", description="", payment_method=None
    ):
        """
        Crée une nouvelle transaction

        Args:
            user: Instance du modèle Shopper
            amount (Decimal): Montant de la transaction
            provider (str): Fournisseur de paiement
            order_id (str): ID de commande associée
            description (str): Description de la transaction
            payment_method: Instance de PaymentMethod

        Returns:
            Transaction: Instance créée
        """
        transaction_id = f"txn_{uuid.uuid4().hex[:12]}"

        transaction = Transaction.objects.create(
            user=user,
            order_id=order_id,
            transaction_id=transaction_id,
            provider=provider,
            payment_method=payment_method,
            amount=amount,
            description=description,
            status="pending",
        )

        logger.info(f"Transaction créée: {transaction_id}")
        return transaction

    @staticmethod
    def update_transaction_status(
        transaction, status, provider_transaction_id="", error_message=""
    ):
        """
        Met à jour le statut d'une transaction

        Args:
            transaction: Instance de Transaction
            status (str): Nouveau statut
            provider_transaction_id (str): ID de transaction du fournisseur
            error_message (str): Message d'erreur si applicable
        """
        transaction.status = status
        transaction.provider_transaction_id = provider_transaction_id
        transaction.error_message = error_message
        transaction.save()

        logger.info(f"Transaction {transaction.transaction_id} mise à jour: {status}")


class UnifiedPaymentService:
    """
    Service unifié pour traiter tous types de paiements
    """

    @staticmethod
    def process_payment(
        user, amount, provider, payment_data, order_id="", description=""
    ):
        """
        Traite un paiement via le fournisseur spécifié

        Args:
            user: Instance du modèle Shopper
            amount (Decimal): Montant du paiement
            provider (str): Fournisseur ('stripe' ou 'paypal')
            payment_data (dict): Données de paiement spécifiques au fournisseur
            order_id (str): ID de commande
            description (str): Description du paiement

        Returns:
            dict: Résultat du traitement
        """
        # Créer la transaction
        transaction = TransactionService.create_transaction(
            user=user,
            amount=amount,
            provider=provider,
            order_id=order_id,
            description=description,
        )

        try:
            if provider == "stripe":
                result = UnifiedPaymentService._process_stripe_payment(
                    transaction, payment_data
                )
            elif provider == "paypal":
                result = UnifiedPaymentService._process_paypal_payment(
                    transaction, payment_data
                )
            else:
                raise PaymentProcessingError(f"Fournisseur non supporté: {provider}")

            return {
                "success": True,
                "transaction": transaction,
                "provider_data": result,
            }

        except PaymentProcessingError as e:
            # Mettre à jour le statut d'erreur
            TransactionService.update_transaction_status(
                transaction, "failed", error_message=str(e)
            )

            return {"success": False, "transaction": transaction, "error": str(e)}

    @staticmethod
    def _process_stripe_payment(transaction, payment_data):
        """Traite un paiement Stripe"""
        # Créer le PaymentIntent
        payment_intent = StripePaymentProcessor.create_payment_intent(
            amount=transaction.amount,
            description=transaction.description,
            metadata={"transaction_id": transaction.transaction_id},
        )

        # Mettre à jour la transaction avec l'ID Stripe
        TransactionService.update_transaction_status(
            transaction, "processing", payment_intent.id
        )

        return payment_intent

    @staticmethod
    def _process_paypal_payment(transaction, payment_data):
        """Traite un paiement PayPal"""
        return_url = payment_data.get("return_url", settings.PAYMENT_SUCCESS_URL)
        cancel_url = payment_data.get("cancel_url", settings.PAYMENT_CANCEL_URL)

        # Créer le paiement PayPal
        payment = PayPalPaymentProcessor.create_payment(
            amount=transaction.amount,
            description=transaction.description,
            return_url=return_url,
            cancel_url=cancel_url,
        )

        # Mettre à jour la transaction avec l'ID PayPal
        TransactionService.update_transaction_status(
            transaction, "processing", payment.id
        )

        return payment
