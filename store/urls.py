from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("product/<str:slug>/", views.product_detail, name="product_detail"),
    path("product/<str:slug>/add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("category/<slug:category_slug>/", views.category_view, name="category"),
    path("cart/", views.cart, name="cart"),
    path("cart/delete/", views.delete_cart, name="delete_cart"),
    path(
        "cart/increase/<int:order_id>/",
        views.increase_quantity,
        name="increase_quantity",
    ),
    path(
        "cart/decrease/<int:order_id>/",
        views.decrease_quantity,
        name="decrease_quantity",
    ),
    path(
        "cart/remove/<int:order_id>/", views.remove_from_cart, name="remove_from_cart"
    ),
    path("checkout/", views.checkout, name="checkout"),
    path("order-confirmation/", views.order_confirmation, name="order_confirmation"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path(
        "order/<int:order_id>/invoice/", views.download_invoice, name="download_invoice"
    ),
    path("order/<int:order_id>/reorder/", views.reorder, name="reorder"),
    path("order/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    # Wishlist URLs
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/add/", views.add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("wishlist/check/", views.check_wishlist_status, name="check_wishlist_status"),
]
