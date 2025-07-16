from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from store.models import Product, Order, Cart, Category


# Configuration de l'interface admin avec style
admin.site.site_header = "🛒 YEE E-Commerce Administration"
admin.site.site_title = "YEE Admin"
admin.site.index_title = "📊 Tableau de bord E-Commerce"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Administration des catégories."""

    list_display = (
        "name",
        "slug",
        "product_count",
        "featured_badge",
        "active_badge",
        "created_at",
        "view_link",
    )
    search_fields = ("name", "description")
    readonly_fields = ("created_at",)
    prepopulated_fields = {"slug": ("name",)}
    actions = ["duplicate_categories", "mark_as_featured", "mark_as_active"]
    list_filter = ("is_featured", "is_active", "created_at")

    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
        ("Affichage", {"fields": ("is_featured", "is_active", "display_order")}),
        ("Style", {"fields": ("color_theme", "icon_class")}),
        (
            "SEO",
            {"fields": ("meta_description", "meta_keywords"), "classes": ("collapse",)},
        ),
        ("Métadonnées", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def product_count(self, obj):
        count = obj.product_count
        total_count = obj.total_product_count
        url = (
            reverse("admin:store_product_changelist") + f"?category__id__exact={obj.id}"
        )
        return format_html(
            '<a href="{}" style="background: #28a745; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; text-decoration: none;">{}/{} produits</a>',
            url,
            count,
            total_count,
        )

    product_count.short_description = "📦 Produits"

    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">⭐ Vedette</span>'
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    featured_badge.short_description = "🌟 Vedette"

    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Actif</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">❌ Inactif</span>'
        )

    active_badge.short_description = "🔄 Statut"

    def view_link(self, obj):
        if obj.slug:
            view_url = reverse("category", args=[obj.slug])
            return format_html(
                '<a href="{}" target="_blank" style="background: #007bff; color: white; padding: 4px 8px; '
                'border-radius: 4px; text-decoration: none; font-size: 11px;">👁️ Voir</a>',
                view_url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-size: 11px;">⚠️ Slug requis</span>'
            )

    view_link.short_description = "Actions"

    def duplicate_categories(self, request, queryset):
        """Action pour dupliquer des catégories"""
        count = 0
        for category in queryset:
            original_name = category.name
            original_slug = category.slug
            category.pk = None
            category.name = f"{original_name} (Copie)"
            category.slug = (
                f"{original_slug}-copie" if original_slug else f"copie-{count}"
            )
            category.save()
            count += 1

        self.message_user(
            request, f"{count} catégorie(s) dupliquée(s) avec succès.", messages.SUCCESS
        )

    duplicate_categories.short_description = "🔄 Dupliquer les catégories sélectionnées"

    def mark_as_featured(self, request, queryset):
        """Marquer comme catégories vedettes"""
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f"{updated} catégorie(s) marquée(s) comme vedettes.",
            messages.SUCCESS,
        )

    mark_as_featured.short_description = "⭐ Marquer comme vedettes"

    def mark_as_active(self, request, queryset):
        """Activer les catégories"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated} catégorie(s) activée(s).", messages.SUCCESS
        )

    mark_as_active.short_description = "✅ Activer"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administration des produits."""

    list_display = (
        "name",
        "category_badge",
        "price_display",
        "stock_display",
        "sales_stats",
        "image_preview",
        "availability_badge",
        "created_at",
        "actions_links",
    )
    list_filter = ("category", "created_at", "stock")
    search_fields = ("name", "description", "slug")
    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "image_preview",
        "sales_summary",
    )
    list_per_page = 20
    actions = ["mark_out_of_stock", "duplicate_products", "bulk_discount"]

    fieldsets = (
        (None, {"fields": ("name", "slug", "category")}),
        ("Prix et Stock", {"fields": ("price", "stock")}),
        ("Description", {"fields": ("description",)}),
        ("Image", {"fields": ("thumbnail", "image_preview")}),
        ("Statistiques", {"fields": ("sales_summary",), "classes": ("collapse",)}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def category_badge(self, obj):
        if obj.category:
            return format_html(
                '<span style="background: {}; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">{}</span>',
                (
                    obj.category.color_theme
                    if hasattr(obj.category, "color_theme")
                    else "#6c757d"
                ),
                obj.category.name,
            )
        return format_html('<span style="color: #6c757d;">Aucune</span>')

    category_badge.short_description = "🏷️ Catégorie"

    def price_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #007bff; font-size: 14px;">{} €</span>',
            "{:.2f}".format(obj.price),
        )

    price_display.short_description = "💰 Prix"

    def stock_display(self, obj):
        if obj.stock > 10:
            color = "#28a745"  # Vert
            icon = "✅"
            status = "En stock"
        elif obj.stock > 0:
            color = "#ffc107"  # Orange
            icon = "⚠️"
            status = "Stock faible"
        else:
            color = "#dc3545"  # Rouge
            icon = "❌"
            status = "Rupture"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {} ({})</span>',
            color,
            icon,
            obj.stock,
            status,
        )

    stock_display.short_description = "📦 Stock"

    def sales_stats(self, obj):
        # Calculer les statistiques de vente
        orders = obj.order_set.filter(ordered=True)
        total_sold = orders.aggregate(total=Sum("quantity"))["total"] or 0
        total_revenue = sum(order.quantity * obj.price for order in orders)

        # Convertir explicitement en types simples
        total_sold = int(total_sold) if total_sold else 0
        total_revenue = float(total_revenue) if total_revenue else 0.0

        # Format string plus simple
        html_content = (
            '<div style="font-size: 11px;">'
            f"<div>📊 {total_sold} vendus</div>"
            f"<div>💰 {total_revenue:.2f} € CA</div>"
            "</div>"
        )

        return format_html(html_content)

    sales_stats.short_description = "📈 Ventes"

    def availability_badge(self, obj):
        if obj.is_available:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Disponible</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">❌ Indisponible</span>'
        )

    availability_badge.short_description = "🔄 Disponibilité"

    def image_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; '
                'object-fit: cover; border-radius: 8px; border: 2px solid #ddd;" />',
                obj.thumbnail.url,
            )
        return format_html('<span style="color: #6c757d;">📷 Pas d\'image</span>')

    image_preview.short_description = "🖼️ Aperçu"

    def sales_summary(self, obj):
        orders = obj.order_set.filter(ordered=True)
        if orders.exists():
            stats = orders.aggregate(
                total_sold=Sum("quantity"),
                avg_quantity=Avg("quantity"),
                order_count=Count("id"),
            )
            total_revenue = sum(order.quantity * obj.price for order in orders)

            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
                '<h4 style="margin-top: 0;">📊 Résumé des ventes</h4>'
                "<p><strong>Total vendu:</strong> {} unités</p>"
                "<p><strong>Nombre de commandes:</strong> {}</p>"
                "<p><strong>Quantité moyenne:</strong> {:.1f} par commande</p>"
                "<p><strong>Chiffre d'affaires:</strong> {:.2f} €</p>"
                "</div>",
                stats["total_sold"] or 0,
                stats["order_count"] or 0,
                stats["avg_quantity"] or 0,
                total_revenue,
            )
        return format_html('<p style="color: #6c757d;">Aucune vente enregistrée</p>')

    sales_summary.short_description = "📊 Résumé des ventes"

    def actions_links(self, obj):
        view_url = reverse("product", args=[obj.slug]) if obj.slug else "#"
        return format_html(
            '<a href="{}" target="_blank" style="background: #007bff; color: white; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px; margin-right: 4px;">👁️ Voir</a>'
            '<a href="#" onclick="alert(\'Modifier le stock\');" '
            'style="background: #28a745; color: white; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px;">📦 Stock</a>',
            view_url,
        )

    actions_links.short_description = "⚙️ Actions"

    def mark_out_of_stock(self, request, queryset):
        """Marquer comme en rupture de stock"""
        updated = queryset.update(stock=0)
        self.message_user(
            request,
            f"{updated} produit(s) marqué(s) en rupture de stock.",
            messages.WARNING,
        )

    mark_out_of_stock.short_description = "❌ Marquer en rupture de stock"

    def duplicate_products(self, request, queryset):
        """Dupliquer les produits sélectionnés"""
        count = 0
        for product in queryset:
            original_name = product.name
            product.pk = None
            product.name = f"{original_name} (Copie)"
            product.slug = f"{product.slug}-copie-{count}"
            product.save()
            count += 1

        self.message_user(
            request, f"{count} produit(s) dupliqué(s) avec succès.", messages.SUCCESS
        )

    duplicate_products.short_description = "🔄 Dupliquer les produits"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Administration des commandes."""

    list_display = (
        "id",
        "user_display",
        "product_link",
        "quantity_display",
        "amount_display",
        "status_display",
        "date_ordered",
        "actions_links",
    )
    list_filter = ("ordered", "date_ordered", "product__category")
    search_fields = ("user__username", "user__email", "product__name")
    readonly_fields = ("date_ordered", "amount_calculation")
    list_per_page = 25
    actions = ["mark_as_ordered", "cancel_orders"]

    fieldsets = (
        (None, {"fields": ("user", "product", "quantity", "ordered")}),
        ("Dates", {"fields": ("date_ordered", "created_at")}),
        ("Calculs", {"fields": ("amount_calculation",), "classes": ("collapse",)}),
    )

    def user_display(self, obj):
        return format_html(
            '<a href="{}" style="color: #007bff; text-decoration: none;">'
            '<span style="font-weight: bold;">👤 {}</span></a>',
            reverse("admin:accounts_shopper_change", args=[obj.user.id]),
            obj.user.username,
        )

    user_display.short_description = "👤 Client"

    def product_link(self, obj):
        return format_html(
            '<a href="{}" style="color: #007bff; text-decoration: none;">{}</a>',
            reverse("admin:store_product_change", args=[obj.product.id]),
            obj.product.name,
        )

    product_link.short_description = "📦 Produit"

    def quantity_display(self, obj):
        return format_html(
            '<span style="background: #17a2b8; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{} unités</span>',
            obj.quantity,
        )

    quantity_display.short_description = "🔢 Quantité"

    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #28a745; font-size: 14px;">{} €</span>',
            f"{obj.total_price:.2f}",
        )

    amount_display.short_description = "💰 Montant"

    def status_display(self, obj):
        if obj.ordered:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Commandé</span>'
            )
        else:
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">🛒 En panier</span>'
            )

    status_display.short_description = "📋 Statut"

    def amount_calculation(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
            '<h4 style="margin-top: 0;">💰 Calcul du montant</h4>'
            "<p><strong>Prix unitaire:</strong> {:.2f} €</p>"
            "<p><strong>Quantité:</strong> {} unités</p>"
            "<p><strong>Total:</strong> {:.2f} €</p>"
            "</div>",
            obj.product.price,
            obj.quantity,
            obj.total_price,
        )

    amount_calculation.short_description = "💰 Calculs"

    def actions_links(self, obj):
        if not obj.ordered:
            return format_html(
                '<a href="#" onclick="alert(\'Valider la commande\');" '
                'style="background: #28a745; color: white; padding: 2px 6px; '
                'border-radius: 4px; text-decoration: none; font-size: 10px;">✅ Valider</a>'
            )
        return format_html(
            '<a href="#" onclick="alert(\'Annuler la commande\');" '
            'style="background: #dc3545; color: white; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px;">❌ Annuler</a>'
        )

    actions_links.short_description = "⚙️ Actions"

    def mark_as_ordered(self, request, queryset):
        """Marquer les commandes comme finalisées"""
        from django.utils import timezone

        updated = queryset.update(ordered=True, date_ordered=timezone.now())
        self.message_user(
            request, f"{updated} commande(s) finalisée(s).", messages.SUCCESS
        )

    mark_as_ordered.short_description = "✅ Finaliser les commandes"

    def cancel_orders(self, request, queryset):
        """Annuler les commandes"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} commande(s) annulée(s).", messages.WARNING)

    cancel_orders.short_description = "❌ Annuler les commandes"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Administration des paniers."""

    list_display = (
        "user_display",
        "items_count",
        "total_value",
        "last_activity",
        "status_badge",
    )
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "detailed_summary")
    filter_horizontal = ("orders",)
    list_filter = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user", "orders")}),
        ("Résumé", {"fields": ("detailed_summary",)}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_display(self, obj):
        return format_html(
            '<a href="{}" style="color: #007bff; text-decoration: none;">'
            '<span style="font-weight: bold;">👤 {}</span></a>',
            reverse("admin:accounts_shopper_change", args=[obj.user.id]),
            obj.user.username,
        )

    user_display.short_description = "👤 Client"

    def items_count(self, obj):
        count = obj.total_items
        return format_html(
            '<span style="background: #17a2b8; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{} articles</span>',
            count,
        )

    items_count.short_description = "🛒 Articles"

    def total_value(self, obj):
        total = obj.total_price
        return format_html(
            '<span style="font-weight: bold; color: #28a745; font-size: 14px;">{} €</span>',
            f"{total:.2f}",
        )

    total_value.short_description = "💰 Total"

    def last_activity(self, obj):
        return format_html(
            '<span style="color: #6c757d; font-size: 11px;">{}</span>',
            obj.updated_at.strftime("%d/%m/%Y %H:%M") if obj.updated_at else "N/A",
        )

    last_activity.short_description = "🕐 Dernière activité"

    def status_badge(self, obj):
        if obj.total_items > 0:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">🛒 Actif</span>'
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">📭 Vide</span>'
        )

    status_badge.short_description = "📊 Statut"

    def detailed_summary(self, obj):
        orders = obj.orders.all()
        if orders.exists():
            summary_html = (
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
            )
            summary_html += '<h4 style="margin-top: 0;">🛒 Contenu du panier</h4>'

            for order in orders:
                summary_html += f"""
                <div style="border-bottom: 1px solid #dee2e6; padding: 5px 0;">
                    <strong>{order.product.name}</strong><br>
                    <small>Prix: {order.product.price:.2f} € × {order.quantity} = {order.total_price:.2f} €</small>
                </div>
                """

            summary_html += f'<div style="margin-top: 10px; font-weight: bold;">Total: {obj.total_price:.2f} €</div>'
            summary_html += "</div>"

            return format_html(summary_html)

        return format_html('<p style="color: #6c757d;">Panier vide</p>')

    detailed_summary.short_description = "� Détail du panier"
