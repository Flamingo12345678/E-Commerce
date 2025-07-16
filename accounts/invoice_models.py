"""
Modèles pour le système de facturation avec Stripe et PayPal
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta


class InvoiceTemplate(models.Model):
    """
    Modèle pour gérer les templates de factures personnalisables
    """

    name = models.CharField(max_length=100, verbose_name="Nom du template")
    company_name = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    company_address = models.TextField(verbose_name="Adresse de l'entreprise")
    company_logo = models.ImageField(
        upload_to="invoice_templates/",
        blank=True,
        null=True,
        verbose_name="Logo de l'entreprise",
    )
    footer_text = models.TextField(blank=True, verbose_name="Texte de pied de page")
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00, verbose_name="Taux de TVA (%)"
    )
    payment_terms = models.TextField(
        default="Paiement à réception de facture", verbose_name="Conditions de paiement"
    )
    is_default = models.BooleanField(default=False, verbose_name="Template par défaut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template de facture"
        verbose_name_plural = "Templates de factures"
        ordering = ["-is_default", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            # S'assurer qu'il n'y a qu'un seul template par défaut
            InvoiceTemplate.objects.filter(is_default=True).exclude(id=self.id).update(
                is_default=False
            )
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """
    Modèle principal pour les factures
    """

    INVOICE_STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("sent", "Envoyée"),
        ("paid", "Payée"),
        ("overdue", "En retard"),
        ("cancelled", "Annulée"),
        ("refunded", "Remboursée"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
        ("bank_transfer", "Virement bancaire"),
        ("cash", "Espèces"),
        ("check", "Chèque"),
        ("other", "Autre"),
    ]

    # Identifiants
    invoice_number = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de facture"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Relations
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name="Client",
    )
    template = models.ForeignKey(
        InvoiceTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Template",
    )

    # Informations de base
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default="draft",
        verbose_name="Statut",
    )
    issue_date = models.DateField(default=timezone.now, verbose_name="Date d'émission")
    due_date = models.DateField(verbose_name="Date d'échéance")

    # Montants
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Sous-total HT"
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Montant TVA"
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Remise"
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Total TTC"
    )

    # Informations de paiement
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        verbose_name="Méthode de paiement",
    )
    paid_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de paiement"
    )

    # Intégration avec les systèmes de paiement
    stripe_invoice_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID facture Stripe"
    )
    paypal_invoice_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID facture PayPal"
    )

    # Métadonnées
    notes = models.TextField(blank=True, verbose_name="Notes")
    terms_and_conditions = models.TextField(blank=True, verbose_name="CGV")
    currency = models.CharField(max_length=3, default="EUR", verbose_name="Devise")

    # Tracking
    sent_date = models.DateTimeField(null=True, blank=True, verbose_name="Date d'envoi")
    viewed_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de première consultation"
    )
    reminder_sent_count = models.PositiveIntegerField(
        default=0, verbose_name="Nombre de rappels envoyés"
    )
    last_reminder_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Date du dernier rappel"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["customer"]),
        ]

    def __str__(self):
        return f"Facture {self.invoice_number} - {self.customer.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=30)

        # Calculer le total automatiquement
        self.calculate_totals()

        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Génère un numéro de facture unique"""
        year = timezone.now().year
        # Compter les factures de l'année
        count = Invoice.objects.filter(created_at__year=year).count() + 1

        return f"INV-{year}-{count:04d}"

    def calculate_totals(self):
        """Calcule les totaux de la facture"""
        # Calculer le sous-total à partir des lignes
        self.subtotal = sum(
            item.quantity * item.unit_price for item in self.items.all()
        )

        # Calculer la TVA
        if hasattr(self, "template") and self.template:
            tax_rate = self.template.tax_rate / 100
        else:
            tax_rate = Decimal("0.20")  # 20% par défaut

        self.tax_amount = (self.subtotal - self.discount_amount) * tax_rate
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount

    @property
    def is_overdue(self):
        """Vérifie si la facture est en retard"""
        return self.status in ["sent"] and self.due_date < timezone.now().date()

    @property
    def days_until_due(self):
        """Nombre de jours avant échéance"""
        if self.status == "paid":
            return 0
        return (self.due_date - timezone.now().date()).days

    @property
    def can_be_paid(self):
        """Vérifie si la facture peut être payée"""
        return self.status in ["sent", "overdue"]

    def mark_as_paid(self, payment_method=None, payment_date=None):
        """Marque la facture comme payée"""
        self.status = "paid"
        self.paid_date = payment_date or timezone.now()
        if payment_method:
            self.payment_method = payment_method
        self.save()

    def send_invoice(self):
        """Marque la facture comme envoyée"""
        if self.status == "draft":
            self.status = "sent"
            self.sent_date = timezone.now()
            self.save()

    def get_payment_url(self):
        """Retourne l'URL de paiement pour cette facture"""
        from django.urls import reverse

        return reverse("invoice_pay", kwargs={"uuid": self.uuid})


class InvoiceItem(models.Model):
    """
    Lignes d'une facture
    """

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="items", verbose_name="Facture"
    )
    product = models.ForeignKey(
        "store.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Produit",
    )
    description = models.CharField(max_length=255, verbose_name="Description")
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=1.00, verbose_name="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix unitaire"
    )

    # Calculé automatiquement
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Total ligne"
    )

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}€"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Recalculer les totaux de la facture
        self.invoice.calculate_totals()
        self.invoice.save()


class InvoicePayment(models.Model):
    """
    Modèle pour tracker les paiements des factures
    """

    PAYMENT_STATUS_CHOICES = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
        ("cancelled", "Annulé"),
        ("refunded", "Remboursé"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Facture",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Montant"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=Invoice.PAYMENT_METHOD_CHOICES,
        verbose_name="Méthode de paiement",
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
        verbose_name="Statut",
    )

    # Intégration avec les systèmes de paiement
    stripe_payment_intent_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="PaymentIntent Stripe"
    )
    paypal_payment_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Payment ID PayPal"
    )

    # Métadonnées
    transaction_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Frais de transaction",
    )
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True, verbose_name="Notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de completion"
    )

    class Meta:
        verbose_name = "Paiement de facture"
        verbose_name_plural = "Paiements de factures"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Paiement {self.amount}€ - {self.invoice.invoice_number}"

    def mark_as_completed(self):
        """Marque le paiement comme terminé"""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

        # Vérifier si la facture est entièrement payée
        total_paid = sum(
            payment.amount
            for payment in self.invoice.payments.filter(status="completed")
        )

        if total_paid >= self.invoice.total_amount:
            self.invoice.mark_as_paid(
                payment_method=self.payment_method, payment_date=self.completed_at
            )


class InvoiceReminder(models.Model):
    """
    Modèle pour gérer les rappels automatiques de factures
    """

    REMINDER_TYPES = [
        ("before_due", "Avant échéance"),
        ("on_due_date", "Le jour de l'échéance"),
        ("after_due", "Après échéance"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="Facture",
    )
    reminder_type = models.CharField(
        max_length=20, choices=REMINDER_TYPES, verbose_name="Type de rappel"
    )
    days_offset = models.IntegerField(
        verbose_name="Décalage en jours"
    )  # Négatif pour avant, positif pour après
    sent_date = models.DateTimeField(null=True, blank=True, verbose_name="Date d'envoi")
    email_sent = models.BooleanField(default=False, verbose_name="Email envoyé")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rappel de facture"
        verbose_name_plural = "Rappels de factures"
        ordering = ["days_offset"]
        unique_together = ["invoice", "reminder_type", "days_offset"]

    def __str__(self):
        return (
            f"Rappel {self.get_reminder_type_display()} - {self.invoice.invoice_number}"
        )

    @property
    def scheduled_date(self):
        """Date programmée pour l'envoi du rappel"""
        return self.invoice.due_date + timedelta(days=self.days_offset)

    @property
    def should_be_sent(self):
        """Vérifie si le rappel doit être envoyé"""
        return (
            not self.email_sent
            and timezone.now().date() >= self.scheduled_date
            and self.invoice.status in ["sent", "overdue"]
        )


class RecurringInvoiceTemplate(models.Model):
    """
    Modèle pour les factures récurrentes
    """

    FREQUENCY_CHOICES = [
        ("weekly", "Hebdomadaire"),
        ("monthly", "Mensuelle"),
        ("quarterly", "Trimestrielle"),
        ("yearly", "Annuelle"),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom du modèle")
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_invoices",
        verbose_name="Client",
    )
    template = models.ForeignKey(
        InvoiceTemplate,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Template de facture",
    )

    # Configuration de récurrence
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Fréquence"
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    next_invoice_date = models.DateField(verbose_name="Prochaine facture")

    # Configuration du contenu
    description_template = models.TextField(verbose_name="Template de description")
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Montant"
    )

    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    auto_send = models.BooleanField(default=False, verbose_name="Envoi automatique")

    # Tracking
    invoices_generated = models.PositiveIntegerField(
        default=0, verbose_name="Factures générées"
    )
    last_generated = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière génération"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facture récurrente"
        verbose_name_plural = "Factures récurrentes"
        ordering = ["next_invoice_date"]

    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"

    def calculate_next_date(self):
        """Calcule la prochaine date de facturation"""
        from dateutil.relativedelta import relativedelta

        if self.frequency == "weekly":
            return self.next_invoice_date + timedelta(weeks=1)
        elif self.frequency == "monthly":
            return self.next_invoice_date + relativedelta(months=1)
        elif self.frequency == "quarterly":
            return self.next_invoice_date + relativedelta(months=3)
        elif self.frequency == "yearly":
            return self.next_invoice_date + relativedelta(years=1)

        return self.next_invoice_date

    def should_generate_invoice(self):
        """Vérifie si une nouvelle facture doit être générée"""
        return (
            self.is_active
            and timezone.now().date() >= self.next_invoice_date
            and (not self.end_date or self.next_invoice_date <= self.end_date)
        )

    def generate_invoice(self):
        """Génère une nouvelle facture basée sur ce template"""
        if not self.should_generate_invoice():
            return None

        invoice = Invoice.objects.create(
            customer=self.customer,
            template=self.template,
            due_date=self.next_invoice_date + timedelta(days=30),
            notes=self.description_template,
            status="draft" if not self.auto_send else "sent",
        )

        # Ajouter une ligne de facture
        InvoiceItem.objects.create(
            invoice=invoice,
            description=self.description_template,
            quantity=1,
            unit_price=self.amount,
        )

        # Mettre à jour les compteurs
        self.invoices_generated += 1
        self.last_generated = timezone.now()
        self.next_invoice_date = self.calculate_next_date()
        self.save()

        # Envoyer automatiquement si configuré
        if self.auto_send:
            invoice.send_invoice()

        return invoice
