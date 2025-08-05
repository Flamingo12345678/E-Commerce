from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum
from accounts.models import (
    Shopper,
    Address,
    PaymentMethod,
    Transaction,
    OrphanTransaction,
    WebhookLog,
    EmailTemplate,
    EmailTestSend,
)
from .email_services import EmailService

# Import des modèles et interface d'administration pour les factures
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


class NotificationDashboardAdmin:
    """Dashboard centralisé pour la gestion des notifications"""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "notifications/dashboard/",
                self.admin_site.admin_view(self.notifications_dashboard),
                name="notifications_dashboard",
            ),
            path(
                "notifications/compose/",
                self.admin_site.admin_view(self.compose_newsletter),
                name="compose_newsletter",
            ),
            path(
                "notifications/subscribers/",
                self.admin_site.admin_view(self.view_subscribers),
                name="view_subscribers",
            ),
            path(
                "notifications/stats/",
                self.admin_site.admin_view(self.email_stats),
                name="email_stats",
            ),
        ]
        return custom_urls + urls

    def notifications_dashboard(self, request):
        """Dashboard principal des notifications"""
        stats = self.get_notification_stats()
        context = {
            "title": "Dashboard Notifications",
            "stats": stats,
            "has_permission": True,
        }
        return render(request, "admin/notifications_dashboard.html", context)

    def compose_newsletter(self, request):
        """Vue pour composer et envoyer une newsletter"""
        from django.contrib import messages

        if request.method == "POST":
            subject = request.POST.get("subject", "").strip()
            content = request.POST.get("content", "").strip()
            send_test = request.POST.get("send_test", False)
            test_email = request.POST.get("test_email", "").strip()

            if not subject or not content:
                messages.error(request, "Le sujet et le contenu sont obligatoires")
                return render(request, "admin/newsletter_compose.html")

            try:
                if send_test and test_email:
                    try:
                        test_user = Shopper.objects.get(email=test_email)
                        EmailService.send_newsletter(subject, content, [test_user])
                        messages.success(
                            request, f"Newsletter de test envoyée à {test_email}"
                        )
                    except Shopper.DoesNotExist:
                        messages.error(
                            request, f"Utilisateur avec l'email {test_email} non trouvé"
                        )
                else:
                    recipients = Shopper.objects.filter(
                        newsletter_subscription=True,
                        email_notifications=True,
                        is_active=True,
                    )

                    sent_count, error_count = EmailService.send_newsletter(
                        subject, content, recipients
                    )

                    messages.success(
                        request,
                        f"Newsletter envoyée ! {sent_count} succès, {error_count} erreurs",
                    )

                    if error_count > 0:
                        messages.warning(
                            request, f"⚠️ {error_count} erreurs lors de l'envoi"
                        )

            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi : {str(e)}")

        # Statistiques pour l'affichage
        total_users = Shopper.objects.filter(is_active=True).count()
        newsletter_subscribers = Shopper.objects.filter(
            newsletter_subscription=True,
            email_notifications=True,
            is_active=True,
        ).count()

        context = {
            "title": "Composer une newsletter",
            "total_users": total_users,
            "newsletter_subscribers": newsletter_subscribers,
        }

        return render(request, "admin/newsletter_compose.html", context)

    def view_subscribers(self, request):
        """Vue pour voir les abonnés à la newsletter"""
        subscribers = Shopper.objects.filter(
            newsletter_subscription=True, is_active=True
        ).order_by("-date_joined")

        context = {
            "title": "Abonnés à la newsletter",
            "subscribers": subscribers,
            "total_count": subscribers.count(),
        }

        return render(request, "admin/newsletter_subscribers.html", context)

    def email_stats(self, request):
        """Statistiques détaillées des emails"""
        stats = self.get_detailed_stats()
        context = {
            "title": "Statistiques Email",
            "stats": stats,
        }
        return render(request, "admin/email_stats.html", context)

    def get_notification_stats(self):
        """Récupère les statistiques de base des notifications"""
        total_users = Shopper.objects.filter(is_active=True).count()
        newsletter_subs = Shopper.objects.filter(
            newsletter_subscription=True, is_active=True
        ).count()
        email_enabled = Shopper.objects.filter(
            email_notifications=True, is_active=True
        ).count()

        return {
            "total_users": total_users,
            "newsletter_subscribers": newsletter_subs,
            "email_notifications_enabled": email_enabled,
            "newsletter_rate": round(
                (newsletter_subs / total_users * 100) if total_users > 0 else 0, 1
            ),
            "email_rate": round((email_enabled / total_users * 100) if total_users > 0 else 0, 1),
        }

    def get_detailed_stats(self):
        """Récupère des statistiques détaillées"""
        base_stats = self.get_notification_stats()

        # Statistiques par mois (utilisateurs récents)
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        recent_users = Shopper.objects.filter(
            date_joined__gte=last_30_days, is_active=True
        ).count()

        recent_newsletter_subs = Shopper.objects.filter(
            date_joined__gte=last_30_days,
            newsletter_subscription=True,
            is_active=True,
        ).count()

        base_stats.update(
            {
                "recent_users_30d": recent_users,
                "recent_newsletter_subs_30d": recent_newsletter_subs,
                "recent_newsletter_rate": round(
                    (recent_newsletter_subs / recent_users * 100)
                    if recent_users > 0
                    else 0,
                    1,
                ),
            }
        )

        return base_stats


@admin.register(Shopper)
class ShopperAdmin(NotificationDashboardAdmin, UserAdmin):
    """Interface d'administration personnalisée pour les clients avec dashboard de notifications intégré"""

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


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates d'emails"""
    
    list_display = (
        'template_badge',
        'subject_display', 
        'is_active_badge',
        'last_modified',
        'actions_links'
    )
    
    list_filter = ('is_active', 'name', 'last_modified')
    search_fields = ('subject', 'html_content')
    
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'subject', 'is_active')
        }),
        ('Contenu HTML', {
            'fields': ('html_content',),
            'classes': ('wide',)
        }),
        ('Informations', {
            'fields': ('last_modified', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('last_modified', 'created_at')
    
    actions = ['load_templates_from_files', 'activate_templates']
    
    def template_badge(self, obj):
        colors = {
            'welcome': '#28a745',
            'order_confirmation': '#007bff', 
            'order_status_update': '#ffc107',
            'newsletter': '#17a2b8'
        }
        icons = {
            'welcome': '🎉',
            'order_confirmation': '📋',
            'order_status_update': '📦', 
            'newsletter': '📰'
        }
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">'
            '{} {}</span>',
            colors.get(obj.name, '#6c757d'),
            icons.get(obj.name, '📧'),
            obj.get_name_display()
        )
    
    template_badge.short_description = "📧 Type"
    
    def subject_display(self, obj):
        return format_html(
            '<strong style="color: #333;">{}</strong>',
            obj.subject[:60] + '...' if len(obj.subject) > 60 else obj.subject
        )
    
    subject_display.short_description = "Sujet"
    
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
    
    is_active_badge.short_description = "Statut"
    
    def actions_links(self, obj):
        return format_html(
            '<a href="/admin/accounts/emailtemplate/{}/preview/" '
            'style="background: #17a2b8; color: white; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px; margin-right: 5px;">'
            '👁️ Aperçu</a>'
            '<a href="/admin/accounts/emailtemplate/{}/test/" '
            'style="background: #ffc107; color: black; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px;">'
            '🧪 Test</a>',
            obj.pk, obj.pk
        )
    
    actions_links.short_description = "Actions"
    
    def load_templates_from_files(self, request, queryset):
        """Action pour charger les templates depuis les fichiers"""
        try:
            loaded_count = self._load_existing_templates()
            self.message_user(request, f"{loaded_count} template(s) chargé(s) depuis les fichiers avec succès!")
        except Exception as e:
            self.message_user(request, f"Erreur: {str(e)}", level=40)  # ERROR level
    
    load_templates_from_files.short_description = "🔄 Recharger depuis les fichiers"
    
    def activate_templates(self, request, queryset):
        """Active les templates sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} template(s) activé(s)")
    
    activate_templates.short_description = "✅ Activer les templates"
    
    def _load_existing_templates(self):
        """Charge les templates existants depuis les fichiers"""
        import os
        from django.conf import settings
        
        template_info = {
            'welcome': {
                'subject': '🎉 Bienvenue chez YEE Codes !',
                'path': 'emails/welcome.html'
            },
            'order_confirmation': {
                'subject': '✅ Confirmation de votre commande - YEE Codes',
                'path': 'emails/order_confirmation.html'
            },
            'order_status_update': {
                'subject': '📦 Mise à jour de votre commande - YEE Codes',
                'path': 'emails/order_status_update.html'
            },
            'newsletter': {
                'subject': '📰 Newsletter YEE Codes',
                'path': 'emails/newsletter.html'
            },
        }
        
        loaded_count = 0
        
        for template_name, info in template_info.items():
            template_path = os.path.join(settings.BASE_DIR, 'templates', info['path'])
            
            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Créer ou mettre à jour le template en base
                    template_obj, created = EmailTemplate.objects.get_or_create(
                        name=template_name,
                        defaults={
                            'subject': info['subject'],
                            'html_content': content,
                            'is_active': True
                        }
                    )
                    
                    if not created:
                        # Mettre à jour le contenu s'il a changé
                        template_obj.html_content = content
                        template_obj.save()
                    
                    loaded_count += 1
                        
                except Exception as e:
                    print(f"Erreur lors du chargement du template {template_name}: {e}")
        
        return loaded_count


@admin.register(EmailTestSend)  
class EmailTestSendAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tests d'emails"""
    
    list_display = (
        'template_info',
        'test_email', 
        'success_badge',
        'sent_at'
    )
    
    list_filter = ('success', 'template__name', 'sent_at')
    search_fields = ('test_email', 'error_message')
    readonly_fields = ('sent_at', 'success', 'error_message')
    
    def template_info(self, obj):
        return format_html(
            '<strong>{}</strong>',
            obj.template.get_name_display()
        )
    
    template_info.short_description = "Template"
    
    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Succès</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">❌ Échec</span>'
        )
    
    success_badge.short_description = "Résultat"
