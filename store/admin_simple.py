from django.contrib import admin

from store.models import Product, Order, Cart, Category


# Configuration de l'interface admin principale
admin.site.site_header = "YEE E-Commerce Administration"
admin.site.site_title = "YEE Admin"
admin.site.index_title = "Tableau de bord"


# ADMIN ULTRA-SIMPLE POUR DÉBOGAGE
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user",)
