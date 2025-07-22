from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from .models import (
    Category,
    Product,
    ProductVariant,
    Order,
    Cart,
    Wishlist,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("size", "stock", "price")
    min_num = 0
    verbose_name = "Variante"
    verbose_name_plural = "Variantes"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active"]
    ordering = ["name"]
    date_hierarchy = "created_at"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "price",
        "image_preview",
        "variant_count",
        "total_stock",
        "is_available",
        "created_at",
    ]
    list_filter = ["category", "created_at", "price"]
    search_fields = ["name", "description", "category__name"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["price"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    inlines = [ProductVariantInline]
    readonly_fields = ["created_at", "updated_at"]

    def image_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />',
                obj.thumbnail.url,
            )
        return format_html('<span style="color: #999;">Pas d\'image</span>')

    image_preview.short_description = "Aperçu"

    def variant_count(self, obj):
        count = obj.variants.count()
        if count > 0:
            return format_html(
                '<span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
                count,
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">0</span>'
        )

    variant_count.short_description = "Variantes"

    def total_stock(self, obj):
        total = obj.variants.aggregate(total=Sum("stock"))["total"] or 0
        color = "#28a745" if total > 10 else "#ffc107" if total > 0 else "#dc3545"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, total
        )

    total_stock.short_description = "Stock total"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "description",
                    "price",
                    "thumbnail",
                    "shoe_size",
                )
            },
        ),
        (
            "Métadonnées",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "size", "stock", "price", "stock_status"]
    list_filter = ["product__category", "size", "stock"]
    search_fields = ["product__name", "size"]
    list_editable = ["stock", "price"]
    ordering = ["product__name", "size"]

    def stock_status(self, obj):
        if obj.stock > 10:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✅ En stock</span>'
            )
        elif obj.stock > 0:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 2px 8px; border-radius: 12px; font-size: 11px;">⚠️ Faible</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">❌ Épuisé</span>'
            )

    stock_status.short_description = "Statut"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "total_items", "total_price", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__username", "user__email"]
    ordering = ["-updated_at"]
    readonly_fields = ["created_at", "updated_at", "detailed_summary"]

    def total_items(self, obj):
        return obj.total_items

    total_items.short_description = "Articles"

    def total_price(self, obj):
        return f"{obj.total_price:.2f} €"

    total_price.short_description = "Total"

    def detailed_summary(self, obj):
        orders = obj.orders.filter(ordered=False)
        if not orders.exists():
            return format_html('<p style="color: #6c757d;">Panier vide</p>')

        html_content = []
        total = 0

        for order in orders:
            subtotal = order.quantity * order.product.price
            total += subtotal
            html_content.append(
                f"""
                <div style="border-bottom: 1px solid #dee2e6; padding: 8px 0;">
                    <strong>{order.product.name}</strong>
                    {f" - Taille: {order.size}" if order.size else ""}
                    <br>
                    <small>Quantité: {order.quantity} × {order.product.price:.2f}€ = {subtotal:.2f}€</small>
                </div>
                """
            )

        html_content.append(
            f"""
            <div style="margin-top: 10px; padding-top: 10px; border-top: 2px solid #007bff;">
                <strong style="color: #007bff;">Total: {total:.2f}€</strong>
            </div>
            """
        )

        return format_html("".join(html_content))

    detailed_summary.short_description = "🛒 Détail du panier"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "product",
        "size",
        "quantity",
        "total_price",
        "ordered",
        "created_at",
    ]
    list_filter = ["ordered", "created_at", "product__category", "size"]
    search_fields = ["user__username", "product__name", "size"]
    list_editable = ["ordered"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def total_price(self, obj):
        total = obj.quantity * obj.product.price
        return f"{total:.2f} €"

    total_price.short_description = "Total"

    readonly_fields = ["created_at"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "product",
                    "size",
                    "quantity",
                    "ordered",
                )
            },
        ),
        (
            "Informations",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Administration des listes de souhaits avec filtres et recherche"""

    list_display = ["user", "product", "created_at", "product_price", "product_status"]
    list_filter = ["created_at", "product__category"]
    search_fields = ["user__username", "user__email", "product__name"]
    ordering = ["-created_at"]
    list_per_page = 20

    def product_price(self, obj):
        """Affiche le prix du produit"""
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{:.2f} €</span>',
            obj.product.price,
        )

    product_price.short_description = "💰 Prix"

    def product_status(self, obj):
        """Affiche le statut du produit"""
        if obj.product.is_available:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Disponible</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">❌ Indisponible</span>'
            )

    product_status.short_description = "📊 Statut"

    fieldsets = (
        (None, {"fields": ("user", "product")}),
        ("Informations", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    readonly_fields = ["created_at"]
