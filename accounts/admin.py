from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from accounts.models import (
    Shopper,
    Address,
    PaymentMethod,
    Transaction,
    OrphanTransaction,
    WebhookLog,
)

# Import des modèles et interface d'administration pour les factures
from .invoice_models import *
from .invoice_admin import *


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Interface d'administration pour les adresses"""

    list_display = (
        "user",
        "address_type_badge",
        "street",
        "city",
        "postal_code",
        "country",
        "is_default_badge",
        "created_at",
    )

    list_filter = ("address_type", "country", "is_default", "created_at")

    search_fields = ("user__username", "user__email", "street", "city", "postal_code")

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user", "address_type", "is_default")}),
        ("Adresse", {"fields": ("street", "city", "state", "postal_code", "country")}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def address_type_badge(self, obj):
        colors = {"home": "#28a745", "work": "#007bff", "other": "#6c757d"}
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.address_type, "#6c757d"),
            obj.get_address_type_display(),
        )

    address_type_badge.short_description = "📍 Type"

    def is_default_badge(self, obj):
        if obj.is_default:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">⭐ Défaut</span>'
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    is_default_badge.short_description = "🏠 Statut"


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Interface d'administration pour les méthodes de paiement"""

    list_display = (
        "user",
        "card_type_badge",
        "masked_card",
        "cardholder_name",
        "expiry_status",
        "is_default_badge",
        "created_at",
    )

    list_filter = ("card_type", "is_default", "created_at", "expiry_year")

    search_fields = ("user__username", "user__email", "cardholder_name", "last4")

    readonly_fields = ("card_number_hash", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user", "card_type", "is_default")}),
        (
            "Informations de carte",
            {"fields": ("cardholder_name", "last4", "expiry_month", "expiry_year")},
        ),
        ("Sécurité", {"fields": ("card_number_hash",), "classes": ("collapse",)}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def card_type_badge(self, obj):
        colors = {
            "visa": "#1a1f71",
            "mastercard": "#eb001b",
            "amex": "#006fcf",
            "discover": "#ff6000",
            "other": "#6c757d",
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.card_type, "#6c757d"),
            obj.get_card_type_display(),
        )

    card_type_badge.short_description = "💳 Type"

    def masked_card(self, obj):
        return format_html(
            '<span style="font-family: monospace; background: #f8f9fa; padding: 2px 6px; '
            'border-radius: 4px;">**** **** **** {}</span>',
            obj.last4,
        )

    masked_card.short_description = "🔢 Carte"

    def expiry_status(self, obj):
        if obj.is_expired:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">❌ Expirée</span>'
            )
        return format_html(
            '<span style="background: #28a745; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">✅ {}</span>',
            obj.expiry_date,
        )

    expiry_status.short_description = "📅 Expiration"

    def is_default_badge(self, obj):
        if obj.is_default:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">⭐ Défaut</span>'
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    is_default_badge.short_description = "💳 Statut"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les transactions"""

    list_display = (
        "transaction_id_short",
        "user",
        "amount_display",
        "provider_badge",
        "status_badge",
        "created_at",
        "actions_links",
    )

    list_filter = ("provider", "status", "currency", "created_at")

    search_fields = (
        "transaction_id",
        "user__username",
        "user__email",
        "provider_transaction_id",
        "description",
    )

    readonly_fields = (
        "transaction_id",
        "provider_transaction_id",
        "created_at",
        "updated_at",
        "metadata_display",
    )

    fieldsets = (
        (None, {"fields": ("user", "transaction_id", "amount", "currency", "status")}),
        (
            "Paiement",
            {"fields": ("provider", "provider_transaction_id", "payment_method")},
        ),
        ("Commande", {"fields": ("order_id", "description")}),
        ("Frais", {"fields": ("processing_fee",)}),
        ("Erreur", {"fields": ("error_message",), "classes": ("collapse",)}),
        (
            "Métadonnées",
            {
                "fields": ("metadata_display", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def transaction_id_short(self, obj):
        return format_html(
            '<span style="font-family: monospace; background: #f8f9fa; padding: 2px 6px; '
            'border-radius: 4px;" title="{}">{}</span>',
            obj.transaction_id,
            (
                obj.transaction_id[:12] + "..."
                if len(obj.transaction_id) > 12
                else obj.transaction_id
            ),
        )

    transaction_id_short.short_description = "🔑 ID Transaction"

    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #28a745; font-size: 14px;">{} {}</span>',
            f"{obj.amount:.2f}",
            obj.currency,
        )

    amount_display.short_description = "💰 Montant"

    def provider_badge(self, obj):
        colors = {"stripe": "#635bff", "paypal": "#003087", "manual": "#6c757d"}
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.provider, "#6c757d"),
            obj.get_provider_display(),
        )

    provider_badge.short_description = "🏦 Fournisseur"

    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "processing": "#17a2b8",
            "succeeded": "#28a745",
            "failed": "#dc3545",
            "cancelled": "#6c757d",
            "refunded": "#fd7e14",
        }
        icons = {
            "pending": "⏳",
            "processing": "⚡",
            "succeeded": "✅",
            "failed": "❌",
            "cancelled": "🚫",
            "refunded": "↩️",
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{} {}</span>',
            colors.get(obj.status, "#6c757d"),
            icons.get(obj.status, ""),
            obj.get_status_display(),
        )

    status_badge.short_description = "📊 Statut"

    def actions_links(self, obj):
        if obj.status == "succeeded" and obj.provider in ["stripe", "paypal"]:
            return format_html(
                '<a href="#" onclick="alert(\'Remboursement via {}\');" '
                'style="background: #fd7e14; color: white; padding: 2px 6px; '
                'border-radius: 4px; text-decoration: none; font-size: 10px;">↩️ Rembourser</a>',
                obj.provider,
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    actions_links.short_description = "⚙️ Actions"

    def metadata_display(self, obj):
        if obj.metadata:
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; '
                'font-size: 11px; max-height: 200px; overflow-y: auto;">{}</pre>',
                str(obj.metadata),
            )
        return format_html('<span style="color: #6c757d;">Aucune métadonnée</span>')

    metadata_display.short_description = "📋 Métadonnées"


@admin.register(Shopper)
class ShopperAdmin(UserAdmin):
    """Interface d'administration personnalisée pour les clients"""

    # Champs à afficher dans la liste
    list_display = (
        "username",
        "email_display",
        "full_name",
        "phone_number",
        "stats_display",
        "notifications_status",
        "is_active_badge",
        "date_joined",
    )

    # Champs sur lesquels on peut filtrer
    list_filter = (
        "is_active",
        "is_staff",
        "newsletter_subscription",
        "email_notifications",
        "sms_notifications",
        "push_notifications",
        "two_factor_enabled",
        "date_joined",
        "last_login",
    )

    # Champs de recherche
    search_fields = ("username", "first_name", "last_name", "email", "phone_number")

    # Champs à afficher dans le formulaire
    fieldsets = UserAdmin.fieldsets + (
        (
            "Informations personnelles supplémentaires",
            {"fields": ("phone_number", "birth_date", "address")},
        ),
        (
            "Préférences",
            {"fields": ("newsletter_subscription",), "classes": ("collapse",)},
        ),
        (
            "Notifications",
            {
                "fields": (
                    "email_notifications",
                    "sms_notifications",
                    "push_notifications",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Sécurité",
            {"fields": ("two_factor_enabled",), "classes": ("collapse",)},
        ),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    # Champs en lecture seule
    readonly_fields = ("created_at", "updated_at", "date_joined", "last_login")

    # Actions personnalisées
    actions = [
        "enable_email_notifications",
        "disable_email_notifications",
        "activate_newsletter",
    ]

    def email_display(self, obj):
        return format_html(
            '<a href="mailto:{}" style="color: #007bff; text-decoration: none;">{}</a>',
            obj.email,
            obj.email,
        )

    email_display.short_description = "📧 Email"

    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else format_html('<span style="color: #6c757d;">-</span>')

    full_name.short_description = "👤 Nom complet"

    def stats_display(self, obj):
        # Compter les commandes et transactions
        orders_count = obj.order_set.filter(ordered=True).count()
        transactions_count = obj.transactions.filter(status="succeeded").count()
        total_spent = (
            obj.transactions.filter(status="succeeded").aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

        return format_html(
            '<div style="font-size: 11px;">'
            "<div>🛒 {} commandes</div>"
            "<div>💳 {} paiements</div>"
            "<div>💰 {} € dépensés</div>"
            "</div>",
            orders_count,
            transactions_count,
            f"{float(total_spent):.2f}",
        )

    stats_display.short_description = "📊 Statistiques"

    def notifications_status(self, obj):
        status = []
        if obj.email_notifications:
            status.append('<span style="color: #28a745;">📧</span>')
        if obj.sms_notifications:
            status.append('<span style="color: #28a745;">📱</span>')
        if obj.push_notifications:
            status.append('<span style="color: #28a745;">🔔</span>')
        if obj.two_factor_enabled:
            status.append('<span style="color: #ffc107;">🔐</span>')

        return format_html(
            " ".join(status) if status else '<span style="color: #6c757d;">-</span>'
        )

    notifications_status.short_description = "🔔 Notifications"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Actif</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">❌ Inactif</span>'
        )

    is_active_badge.short_description = "👤 Statut"

    def enable_email_notifications(self, request, queryset):
        """Active les notifications email pour les utilisateurs sélectionnés"""
        updated = queryset.update(email_notifications=True)
        self.message_user(
            request,
            f"{updated} utilisateur(s) ont maintenant les notifications email activées.",
        )

    enable_email_notifications.short_description = "📧 Activer les notifications email"

    def disable_email_notifications(self, request, queryset):
        """Désactive les notifications email pour les utilisateurs sélectionnés"""
        updated = queryset.update(email_notifications=False)
        self.message_user(
            request,
            f"{updated} utilisateur(s) ont maintenant les notifications email désactivées.",
        )

    disable_email_notifications.short_description = (
        "📧 Désactiver les notifications email"
    )

    def activate_newsletter(self, request, queryset):
        """Active l'abonnement à la newsletter pour les utilisateurs sélectionnés"""
        updated = queryset.update(newsletter_subscription=True)
        self.message_user(
            request,
            f"{updated} utilisateur(s) sont maintenant abonnés à la newsletter.",
        )

    activate_newsletter.short_description = "📬 Activer la newsletter"

    def get_queryset(self, request):
        """Optimise les requêtes avec select_related et prefetch_related"""
        return (
            super()
            .get_queryset(request)
            .select_related()
            .prefetch_related("transactions", "payment_methods", "addresses")
        )

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}


@admin.register(OrphanTransaction)
class OrphanTransactionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les transactions orphelines"""

    list_display = (
        "provider_transaction_short",
        "provider_badge",
        "amount_display",
        "status_badge",
        "investigated_badge",
        "webhook_received_at",
        "actions_links",
    )

    list_filter = (
        "provider",
        "currency",
        "investigated",
        "webhook_received_at",
    )

    search_fields = (
        "provider_transaction_id",
        "provider",
        "notes",
    )

    readonly_fields = (
        "provider_transaction_id",
        "provider_data_display",
        "webhook_received_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "provider",
                    "provider_transaction_id",
                    "amount",
                    "currency",
                    "status",
                )
            },
        ),
        ("Investigation", {"fields": ("investigated", "notes")}),
        (
            "Données du fournisseur",
            {"fields": ("provider_data_display",), "classes": ("collapse",)},
        ),
        ("Métadonnées", {"fields": ("webhook_received_at",), "classes": ("collapse",)}),
    )

    actions = ["mark_as_investigated", "mark_as_uninvestigated"]

    def provider_transaction_short(self, obj):
        return format_html(
            '<span style="font-family: monospace; background: #f8f9fa; '
            'padding: 2px 6px; border-radius: 4px;" title="{}">{}</span>',
            obj.provider_transaction_id,
            (
                obj.provider_transaction_id[:15] + "..."
                if len(obj.provider_transaction_id) > 15
                else obj.provider_transaction_id
            ),
        )

    provider_transaction_short.short_description = "🔑 ID Transaction"

    def provider_badge(self, obj):
        colors = {"stripe": "#635bff", "paypal": "#003087", "other": "#6c757d"}
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.provider.lower(), "#6c757d"),
            obj.provider.upper(),
        )

    provider_badge.short_description = "🏦 Fournisseur"

    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #dc3545; '
            'font-size: 14px;">⚠️ {} {}</span>',
            f"{obj.amount:.2f}",
            obj.currency,
        )

    amount_display.short_description = "💰 Montant"

    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "processing": "#17a2b8",
            "succeeded": "#28a745",
            "completed": "#28a745",
            "failed": "#dc3545",
            "cancelled": "#6c757d",
            "refunded": "#fd7e14",
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.status.lower(), "#6c757d"),
            obj.status.upper(),
        )

    status_badge.short_description = "📊 Statut"

    def investigated_badge(self, obj):
        if obj.investigated:
            return format_html(
                '<span style="background: #28a745; color: white; '
                'padding: 2px 8px; border-radius: 12px; font-size: 11px;">'
                "✅ Enquêtée</span>"
            )
        return format_html(
            '<span style="background: #dc3545; color: white; '
            'padding: 2px 8px; border-radius: 12px; font-size: 11px;">'
            "⚠️ À enquêter</span>"
        )

    investigated_badge.short_description = "🔍 Investigation"

    def actions_links(self, obj):
        if not obj.investigated:
            return format_html(
                '<a href="?action=mark_investigated&ids={}" '
                'style="background: #17a2b8; color: white; padding: 2px 6px; '
                'border-radius: 4px; text-decoration: none; font-size: 10px;">'
                "🔍 Enquêter</a>",
                obj.id,
            )
        return format_html('<span style="color: #28a745;">✅ Terminé</span>')

    actions_links.short_description = "⚙️ Actions"

    def provider_data_display(self, obj):
        if obj.provider_data:
            import json

            try:
                formatted_data = json.dumps(obj.provider_data, indent=2)
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; '
                    "border-radius: 4px; font-size: 11px; max-height: 400px; "
                    'overflow-y: auto;">{}</pre>',
                    formatted_data,
                )
            except Exception:
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; '
                    "border-radius: 4px; font-size: 11px; max-height: 400px; "
                    'overflow-y: auto;">{}</pre>',
                    str(obj.provider_data),
                )
        return format_html('<span style="color: #6c757d;">Aucune donnée</span>')

    provider_data_display.short_description = "📋 Données du fournisseur"

    def mark_as_investigated(self, request, queryset):
        """Marque les transactions comme enquêtées"""
        updated = queryset.update(investigated=True)
        self.message_user(
            request,
            f"{updated} transaction(s) orpheline(s) marquée(s) comme enquêtée(s).",
        )

    mark_as_investigated.short_description = "🔍 Marquer comme enquêtées"

    def mark_as_uninvestigated(self, request, queryset):
        """Marque les transactions comme non enquêtées"""
        updated = queryset.update(investigated=False)
        self.message_user(
            request,
            f"{updated} transaction(s) orpheline(s) marquée(s) "
            f"comme non enquêtée(s).",
        )

    mark_as_uninvestigated.short_description = "❌ Marquer comme non enquêtées"


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs de webhooks"""

    list_display = (
        "event_id_short",
        "provider_badge",
        "event_type_display",
        "signature_status",
        "processing_status",
        "processing_time_display",
        "received_at",
        "actions_links",
    )

    list_filter = (
        "provider",
        "processed_successfully",
        "signature_valid",
        "received_at",
    )

    search_fields = (
        "event_id",
        "event_type",
        "error_message",
    )

    readonly_fields = (
        "provider",
        "event_type",
        "event_id",
        "payload_display",
        "received_at",
        "processing_time_ms",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "provider",
                    "event_type",
                    "event_id",
                    "signature_valid",
                    "processed_successfully",
                )
            },
        ),
        ("Résultats", {"fields": ("processing_time_ms", "error_message")}),
        ("Payload", {"fields": ("payload_display",), "classes": ("collapse",)}),
        ("Métadonnées", {"fields": ("received_at",), "classes": ("collapse",)}),
    )

    actions = ["retry_failed_webhooks", "clear_old_logs"]

    def event_id_short(self, obj):
        return format_html(
            '<span style="font-family: monospace; background: #f8f9fa; '
            'padding: 2px 6px; border-radius: 4px;" title="{}">{}</span>',
            obj.event_id,
            (obj.event_id[:12] + "..." if len(obj.event_id) > 12 else obj.event_id),
        )

    event_id_short.short_description = "🔑 ID Événement"

    def provider_badge(self, obj):
        colors = {"stripe": "#635bff", "paypal": "#003087"}
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.provider, "#6c757d"),
            obj.get_provider_display(),
        )

    provider_badge.short_description = "🏦 Fournisseur"

    def event_type_display(self, obj):
        return format_html(
            '<span style="font-family: monospace; background: #e9ecef; '
            'padding: 2px 6px; border-radius: 4px; font-size: 11px;">{}</span>',
            obj.event_type,
        )

    event_type_display.short_description = "📡 Type d'événement"

    def signature_status(self, obj):
        if obj.signature_valid:
            return format_html(
                '<span style="background: #28a745; color: white; '
                'padding: 2px 8px; border-radius: 12px; font-size: 11px;">'
                "🔐 Valide</span>"
            )
        return format_html(
            '<span style="background: #dc3545; color: white; '
            'padding: 2px 8px; border-radius: 12px; font-size: 11px;">'
            "⚠️ Invalide</span>"
        )

    signature_status.short_description = "🔐 Signature"

    def processing_status(self, obj):
        if obj.processed_successfully:
            return format_html(
                '<span style="background: #28a745; color: white; '
                'padding: 2px 8px; border-radius: 12px; font-size: 11px;">'
                "✅ Succès</span>"
            )
        return format_html(
            '<span style="background: #dc3545; color: white; '
            'padding: 2px 8px; border-radius: 12px; font-size: 11px;">'
            "❌ Échec</span>"
        )

    processing_status.short_description = "📊 Traitement"

    def processing_time_display(self, obj):
        if obj.processing_time_ms is not None:
            if obj.processing_time_ms < 100:
                color = "#28a745"  # Vert
            elif obj.processing_time_ms < 500:
                color = "#ffc107"  # Jaune
            else:
                color = "#dc3545"  # Rouge

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ms</span>',
                color,
                obj.processing_time_ms,
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    processing_time_display.short_description = "⏱️ Temps"

    def actions_links(self, obj):
        if not obj.processed_successfully and obj.signature_valid:
            return format_html(
                '<a href="#" onclick="alert(\'Fonction de retry non implémentée\');" '
                'style="background: #ffc107; color: black; padding: 2px 6px; '
                'border-radius: 4px; text-decoration: none; font-size: 10px;">'
                "🔄 Retry</a>"
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    actions_links.short_description = "⚙️ Actions"

    def payload_display(self, obj):
        if obj.payload:
            import json

            try:
                formatted_payload = json.dumps(obj.payload, indent=2)
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; '
                    "border-radius: 4px; font-size: 11px; max-height: 400px; "
                    'overflow-y: auto;">{}</pre>',
                    formatted_payload,
                )
            except Exception:
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; '
                    "border-radius: 4px; font-size: 11px; max-height: 400px; "
                    'overflow-y: auto;">{}</pre>',
                    str(obj.payload),
                )
        return format_html('<span style="color: #6c757d;">Aucun payload</span>')

    payload_display.short_description = "📋 Payload"

    def retry_failed_webhooks(self, request, queryset):
        """Marque les webhooks échoués pour retry"""
        failed_count = queryset.filter(
            processed_successfully=False, signature_valid=True
        ).count()
        self.message_user(
            request,
            f"{failed_count} webhook(s) échoué(s) marqué(s) pour retry "
            f"(fonctionnalité à implémenter).",
        )

    retry_failed_webhooks.short_description = "🔄 Retry webhooks échoués"

    def clear_old_logs(self, request, queryset):
        """Supprime les anciens logs (plus de 30 jours)"""
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        old_logs = queryset.filter(received_at__lt=thirty_days_ago)
        count = old_logs.count()
        old_logs.delete()

        self.message_user(
            request,
            f"{count} ancien(s) log(s) supprimé(s) (plus de 30 jours).",
        )

    clear_old_logs.short_description = "🗑️ Nettoyer anciens logs"

    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).order_by("-received_at")
