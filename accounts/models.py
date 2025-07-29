from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings

# Importer les modèles de facturation
from .invoice_models import *  # noqa

# Create your models here.


class Address(models.Model):
    """Modèle pour gérer les adresses des utilisateurs"""

    ADDRESS_TYPES = [
        ("home", "Domicile"),
        ("work", "Travail"),
        ("other", "Autre"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses"
    )
    address_type = models.CharField(
        max_length=10, choices=ADDRESS_TYPES, default="home"
    )
    street = models.CharField(max_length=255, verbose_name="Rue")
    city = models.CharField(max_length=100, verbose_name="Ville")
    state = models.CharField(max_length=100, blank=True, verbose_name="État/Province")
    postal_code = models.CharField(max_length=20, verbose_name="Code postal")
    country = models.CharField(max_length=100, default="France", verbose_name="Pays")
    is_default = models.BooleanField(default=False, verbose_name="Adresse par défaut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.get_address_type_display()} - " f"{self.street}, {self.city}"

    @property
    def full_address(self):
        """Retourne l'adresse complète formatée"""
        parts = [self.street, self.city]
        if self.state:
            parts.append(self.state)
        parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


class Shopper(AbstractUser):
    """
    Utilisateur personnalisé pour les clients du magasin.
    Hérite des champs de base d'AbstractUser et peut être étendu avec des champs supplémentaires.
    """

    # Champs supplémentaires pour les clients
    phone_number = models.CharField(
        max_length=20, blank=True, verbose_name="Numéro de téléphone"
    )
    birth_date = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance"
    )
    address = models.TextField(blank=True, verbose_name="Adresse")
    newsletter_subscription = models.BooleanField(
        default=False, verbose_name="Abonnement à la newsletter"
    )

    # Préférences de notifications
    email_notifications = models.BooleanField(
        default=True, verbose_name="Notifications par email"
    )
    sms_notifications = models.BooleanField(
        default=False, verbose_name="Notifications par SMS"
    )
    push_notifications = models.BooleanField(
        default=True, verbose_name="Notifications push"
    )

    # Sécurité
    two_factor_enabled = models.BooleanField(
        default=False, verbose_name="Authentification à deux facteurs"
    )
    
    # Firebase
    firebase_uid = models.CharField(
        max_length=128, blank=True, null=True, unique=True,
        verbose_name="Firebase UID"
    )

    # Facturation
    stripe_customer_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID Client Stripe"
    )
    paypal_customer_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID Client PayPal"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, null=True, verbose_name="Dernière mise à jour"
    )

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-date_joined"]

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.username})"
        return self.username

    @property
    def full_name(self):
        """Retourne le nom complet ou le nom d'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def display_name(self):
        """Retourne le prénom ou le nom d'utilisateur pour affichage"""
        return self.first_name if self.first_name else self.username

    @property
    def has_complete_profile(self):
        """Vérifie si le profil utilisateur est complet"""
        return all(
            [
                self.first_name,
                self.last_name,
                self.email,
                self.phone_number,
                self.address,
            ]
        )

    @property
    def profile_completion_percentage(self):
        """Calcule le pourcentage de complétion du profil"""
        fields = [
            self.first_name,
            self.last_name,
            self.email,
            self.phone_number,
            self.address,
        ]
        completed_fields = sum(1 for field in fields if field)
        return (completed_fields / len(fields)) * 100

    def get_total_orders(self):
        """Retourne le nombre total de commandes passées"""
        from store.models import Order

        return Order.objects.filter(user=self, ordered=True).count()

    def get_total_spent(self):
        """Calcule le montant total dépensé par le client"""
        from store.models import Order

        orders = Order.objects.filter(user=self, ordered=True)
        return sum(order.quantity * order.product.price for order in orders)


class PaymentMethod(models.Model):
    """
    Modèle pour gérer les méthodes de paiement des utilisateurs
    """

    CARD_TYPES = [
        ("visa", "Visa"),
        ("mastercard", "Mastercard"),
        ("amex", "American Express"),
        ("discover", "Discover"),
        ("other", "Autre"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        verbose_name="Utilisateur",
    )
    card_type = models.CharField(
        max_length=20, choices=CARD_TYPES, verbose_name="Type de carte"
    )
    card_number_hash = models.CharField(
        max_length=64, verbose_name="Hash du numéro de carte"
    )
    last4 = models.CharField(max_length=4, verbose_name="4 derniers chiffres")
    cardholder_name = models.CharField(max_length=100, verbose_name="Nom du porteur")
    expiry_month = models.IntegerField(verbose_name="Mois d'expiration")
    expiry_year = models.IntegerField(verbose_name="Année d'expiration")
    is_default = models.BooleanField(default=False, verbose_name="Méthode par défaut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Méthode de paiement"
        verbose_name_plural = "Méthodes de paiement"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return (
            f"{self.get_card_type_display()} ****{self.last4} - {self.cardholder_name}"
        )

    @property
    def expiry_date(self):
        """Retourne la date d'expiration formatée MM/YY"""
        return f"{self.expiry_month:02d}/{self.expiry_year % 100:02d}"

    @property
    def is_expired(self):
        """Vérifie si la carte est expirée"""
        from datetime import datetime

        now = datetime.now()
        current_year = now.year % 100
        current_month = now.month

        if self.expiry_year < current_year:
            return True
        elif self.expiry_year == current_year and self.expiry_month < current_month:
            return True
        return False

    def save(self, *args, **kwargs):
        # Si cette méthode est définie par défaut, retirer le défaut des autres
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(
                id=self.id
            ).update(is_default=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """
    Modèle pour gérer les transactions de paiement
    """

    PAYMENT_PROVIDERS = [
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
        ("manual", "Manuel"),
    ]

    TRANSACTION_STATUS = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("succeeded", "Réussie"),
        ("failed", "Échouée"),
        ("cancelled", "Annulée"),
        ("refunded", "Remboursée"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Utilisateur",
    )
    order_id = models.CharField(
        max_length=100, blank=True, verbose_name="ID de commande"
    )
    transaction_id = models.CharField(
        max_length=255, unique=True, verbose_name="ID de transaction"
    )
    provider = models.CharField(
        max_length=20, choices=PAYMENT_PROVIDERS, verbose_name="Fournisseur de paiement"
    )
    provider_transaction_id = models.CharField(
        max_length=255, blank=True, verbose_name="ID transaction fournisseur"
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Méthode de paiement",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Montant"
    )
    currency = models.CharField(max_length=3, default="EUR", verbose_name="Devise")
    processing_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Frais de traitement",
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default="pending",
        verbose_name="Statut",
    )
    description = models.TextField(blank=True, verbose_name="Description")
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency} ({self.get_status_display()})"

    @property
    def total_amount(self):
        """Montant total incluant les frais"""
        return self.amount + self.processing_fee

    @property
    def is_successful(self):
        """Vérifie si la transaction est réussie"""
        return self.status == "succeeded"

    @property
    def can_be_refunded(self):
        """Vérifie si la transaction peut être remboursée"""
        return self.status in ["succeeded"] and self.provider in ["stripe", "paypal"]


class OrphanTransaction(models.Model):
    """
    Modèle pour stocker les transactions orphelines reçues via webhooks
    qui ne correspondent à aucune transaction existante dans notre système.
    Utile pour l'audit et le débogage.
    """

    provider = models.CharField(max_length=20, verbose_name="Fournisseur de paiement")
    provider_transaction_id = models.CharField(
        max_length=255, verbose_name="ID transaction fournisseur"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Montant"
    )
    currency = models.CharField(max_length=3, default="EUR", verbose_name="Devise")
    status = models.CharField(max_length=50, verbose_name="Statut")
    provider_data = models.JSONField(verbose_name="Données complètes du fournisseur")
    webhook_received_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Reçu le"
    )
    investigated = models.BooleanField(default=False, verbose_name="Enquête effectuée")
    notes = models.TextField(blank=True, verbose_name="Notes d'investigation")

    class Meta:
        verbose_name = "Transaction orpheline"
        verbose_name_plural = "Transactions orphelines"
        ordering = ["-webhook_received_at"]

    def __str__(self):
        return (
            f"Transaction orpheline {self.provider_transaction_id} - "
            f"{self.provider} - {self.amount} {self.currency}"
        )


class WebhookLog(models.Model):
    """
    Modèle pour logger tous les webhooks reçus pour le débogage
    """

    WEBHOOK_PROVIDERS = [
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
    ]

    provider = models.CharField(
        max_length=20, choices=WEBHOOK_PROVIDERS, verbose_name="Fournisseur"
    )
    event_type = models.CharField(max_length=100, verbose_name="Type d'événement")
    event_id = models.CharField(max_length=255, verbose_name="ID d'événement")
    payload = models.JSONField(verbose_name="Payload complet")
    signature_valid = models.BooleanField(
        default=False, verbose_name="Signature valide"
    )
    processed_successfully = models.BooleanField(
        default=False, verbose_name="Traité avec succès"
    )
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    processing_time_ms = models.IntegerField(
        null=True, blank=True, verbose_name="Temps de traitement (ms)"
    )
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Reçu le")

    class Meta:
        verbose_name = "Log de webhook"
        verbose_name_plural = "Logs de webhooks"
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["provider", "event_type"]),
            models.Index(fields=["received_at"]),
            models.Index(fields=["processed_successfully"]),
        ]

    def __str__(self):
        status = "✓" if self.processed_successfully else "✗"
        return f"{status} {self.provider} - {self.event_type}"
