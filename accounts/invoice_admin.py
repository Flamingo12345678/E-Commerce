"""
Configuration de l'interface d'administration pour les factures
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .invoice_models import (
    InvoiceTemplate,
    Invoice,
    InvoiceItem,
    InvoicePayment,
    RecurringInvoiceTemplate,
    InvoiceReminder,
)


@admin.register(InvoiceTemplate)
class InvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "company_name", "tax_rate", "is_default", "created_at"]
    list_filter = ["is_default", "created_at"]
    search_fields = ["name", "company_name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Informations de base",
            {"fields": ("name", "company_name", "company_address", "company_logo")},
        ),
        (
            "Configuration",
            {"fields": ("tax_rate", "payment_terms", "footer_text", "is_default")},
        ),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ["line_total"]


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    readonly_fields = ["created_at", "completed_at"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "customer",
        "status",
        "total_amount",
        "due_date",
        "is_overdue_display",
        "created_at",
    ]
    list_filter = [
        "status",
        "created_at",
        "due_date",
        "currency",
        "payment_method",
        "template",
    ]
    search_fields = [
        "invoice_number",
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "notes",
    ]
    readonly_fields = [
        "uuid",
        "invoice_number",
        "subtotal",
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
        "sent_date",
        "viewed_date",
        "paid_date",
    ]
    inlines = [InvoiceItemInline, InvoicePaymentInline]

    fieldsets = (
        (
            "Informations de base",
            {
                "fields": (
                    "invoice_number",
                    "uuid",
                    "customer",
                    "template",
                    "status",
                    "currency",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "issue_date",
                    "due_date",
                    "sent_date",
                    "viewed_date",
                    "paid_date",
                )
            },
        ),
        (
            "Montants",
            {
                "fields": (
                    "subtotal",
                    "discount_amount",
                    "tax_amount",
                    "total_amount",
                    "payment_method",
                )
            },
        ),
        (
            "Intégration externe",
            {
                "fields": ("stripe_invoice_id", "paypal_invoice_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Détails",
            {
                "fields": ("notes", "terms_and_conditions"),
            },
        ),
        (
            "Rappels",
            {
                "fields": ("reminder_sent_count", "last_reminder_date"),
                "classes": ("collapse",),
            },
        ),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">En retard</span>'
            )
        elif obj.days_until_due <= 3 and obj.status == "sent":
            return format_html('<span style="color: orange;">Bientôt</span>')
        return "-"

    is_overdue_display.short_description = "État échéance"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("customer", "template")

    actions = ["mark_as_sent", "mark_as_paid", "mark_as_cancelled"]

    def mark_as_sent(self, request, queryset):
        updated = 0
        for invoice in queryset.filter(status="draft"):
            invoice.send_invoice()
            updated += 1

        self.message_user(request, f"{updated} facture(s) marquée(s) comme envoyée(s).")

    mark_as_sent.short_description = "Marquer comme envoyées"

    def mark_as_paid(self, request, queryset):
        updated = 0
        for invoice in queryset.filter(status__in=["sent", "overdue"]):
            invoice.mark_as_paid()
            updated += 1

        self.message_user(request, f"{updated} facture(s) marquée(s) comme payée(s).")

    mark_as_paid.short_description = "Marquer comme payées"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"{updated} facture(s) annulée(s).")

    mark_as_cancelled.short_description = "Annuler les factures"


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ["invoice", "description", "quantity", "unit_price", "line_total"]
    list_filter = ["invoice__status", "invoice__created_at"]
    search_fields = ["description", "invoice__invoice_number"]
    readonly_fields = ["line_total"]


@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = [
        "invoice",
        "amount",
        "payment_method",
        "status",
        "created_at",
        "completed_at",
    ]
    list_filter = ["payment_method", "status", "created_at", "completed_at"]
    search_fields = [
        "invoice__invoice_number",
        "reference",
        "stripe_payment_intent_id",
        "paypal_payment_id",
    ]
    readonly_fields = ["created_at", "completed_at"]

    fieldsets = (
        (
            "Informations de base",
            {"fields": ("invoice", "amount", "payment_method", "status")},
        ),
        (
            "Intégration externe",
            {
                "fields": (
                    "stripe_payment_intent_id",
                    "paypal_payment_id",
                    "transaction_fee",
                )
            },
        ),
        ("Détails", {"fields": ("reference", "notes")}),
        (
            "Métadonnées",
            {"fields": ("created_at", "completed_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(RecurringInvoiceTemplate)
class RecurringInvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "customer",
        "frequency",
        "amount",
        "next_invoice_date",
        "is_active",
        "invoices_generated",
    ]
    list_filter = ["frequency", "is_active", "auto_send", "start_date"]
    search_fields = ["name", "customer__email", "description_template"]
    readonly_fields = [
        "invoices_generated",
        "last_generated",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Informations de base",
            {"fields": ("name", "customer", "template", "amount")},
        ),
        (
            "Configuration de récurrence",
            {
                "fields": (
                    "frequency",
                    "start_date",
                    "end_date",
                    "next_invoice_date",
                    "is_active",
                    "auto_send",
                )
            },
        ),
        ("Contenu", {"fields": ("description_template",)}),
        (
            "Statistiques",
            {
                "fields": ("invoices_generated", "last_generated"),
                "classes": ("collapse",),
            },
        ),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["generate_invoices", "activate_templates", "deactivate_templates"]

    def generate_invoices(self, request, queryset):
        generated = 0
        for template in queryset.filter(is_active=True):
            if template.should_generate_invoice():
                invoice = template.generate_invoice()
                if invoice:
                    generated += 1

        self.message_user(
            request, f"{generated} facture(s) générée(s) depuis les templates."
        )

    generate_invoices.short_description = "Générer les factures"

    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} template(s) activé(s).")

    activate_templates.short_description = "Activer les templates"

    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} template(s) désactivé(s).")

    deactivate_templates.short_description = "Désactiver les templates"


@admin.register(InvoiceReminder)
class InvoiceReminderAdmin(admin.ModelAdmin):
    list_display = [
        "invoice",
        "reminder_type",
        "days_offset",
        "scheduled_date_display",
        "email_sent",
        "sent_date",
    ]
    list_filter = ["reminder_type", "email_sent", "sent_date", "created_at"]
    search_fields = ["invoice__invoice_number"]
    readonly_fields = ["created_at", "scheduled_date_display"]

    def scheduled_date_display(self, obj):
        return obj.scheduled_date.strftime("%d/%m/%Y")

    scheduled_date_display.short_description = "Date programmée"

    actions = ["send_reminders"]

    def send_reminders(self, request, queryset):
        from .invoice_views import send_reminder_email

        sent = 0

        for reminder in queryset.filter(email_sent=False):
            if reminder.should_be_sent:
                try:
                    send_reminder_email(reminder)
                    reminder.email_sent = True
                    reminder.save()
                    sent += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Erreur lors de l'envoi du rappel {reminder.id}: {e}",
                        level="ERROR",
                    )

        self.message_user(request, f"{sent} rappel(s) envoyé(s).")

    send_reminders.short_description = "Envoyer les rappels"


# Personnalisation de l'interface d'administration
admin.site.site_header = "YEE E-Commerce - Gestion des Factures"
admin.site.site_title = "Facturation YEE"
admin.site.index_title = "Administration de la facturation"
