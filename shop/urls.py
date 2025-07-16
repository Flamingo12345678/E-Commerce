"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from shop import settings
from django.views.generic import RedirectView
from store.views import (
    index,
    product_detail,
    add_to_cart,
    cart,
    delete_cart,
    increase_quantity,
    decrease_quantity,
    remove_from_cart,
    checkout,
    order_confirmation,
    order_history,
    order_detail,
    download_invoice,
    reorder,
    cancel_order,
    category_view,
)
from accounts.views import (
    signup,
    logout_user,
    login_user,
    profile,
    change_password,
    export_user_data,
    delete_user_account,
    manage_addresses,
    manage_payment_methods,
    update_notifications,
    setup_two_factor,
    two_factor_qr,
    connect_social_account,
    profile_edit_modal,
)


urlpatterns = [
    path("", index, name="index"),
    path("admin/", admin.site.urls),
    # Include URLs from accounts app (authentication + payment)
    path("accounts/", include("accounts.urls")),
    # Authentication URLs (legacy - to maintain compatibility)
    path("login/", login_user, name="login"),
    path("signup/", signup, name="signup"),
    path("logout/", logout_user, name="logout"),
    path("profile/", profile, name="profile"),
    path("change-password/", change_password, name="change_password"),
    # Nouvelles URLs pour les actions du profil
    path("export-data/", export_user_data, name="export_user_data"),
    path("delete-account/", delete_user_account, name="delete_user_account"),
    path("manage-addresses/", manage_addresses, name="manage_addresses"),
    path(
        "manage-payment-methods/", manage_payment_methods, name="manage_payment_methods"
    ),
    path("update-notifications/", update_notifications, name="update_notifications"),
    path("setup-two-factor/", setup_two_factor, name="setup_two_factor"),
    path("two-factor-qr/", two_factor_qr, name="two_factor_qr"),
    path("connect-social/", connect_social_account, name="connect_social_account"),
    path("profile-edit-modal/", profile_edit_modal, name="profile_edit_modal"),
    # Store URLs
    path("cart/", cart, name="cart"),
    path("cart/delete/", delete_cart, name="delete_cart"),
    path("cart/increase/<int:order_id>/", increase_quantity, name="increase_quantity"),
    path("cart/decrease/<int:order_id>/", decrease_quantity, name="decrease_quantity"),
    path("cart/remove/<int:order_id>/", remove_from_cart, name="remove_from_cart"),
    path("checkout/", checkout, name="checkout"),
    path("order-confirmation/", order_confirmation, name="order_confirmation"),
    path("order-history/", order_history, name="order_history"),
    path("order/<int:order_id>/", order_detail, name="order_detail"),
    path("order/<int:order_id>/invoice/", download_invoice, name="download_invoice"),
    path("order/<int:order_id>/reorder/", reorder, name="reorder"),
    path("order/<int:order_id>/cancel/", cancel_order, name="cancel_order"),
    path("category/<slug:category_slug>/", category_view, name="category"),
    path("product/<str:slug>/", product_detail, name="product"),
    path("product/<str:slug>/add-to-cart/", add_to_cart, name="add_to_cart"),
    # Redirection temporaire pour les anciennes URLs PayPal
    path(
        "payment/paypal/execute/",
        RedirectView.as_view(url="/accounts/payment/paypal/execute/", permanent=False),
        name="legacy_paypal_execute",
    ),
    # Redirection temporaire pour l'ancienne URL order-detail
    path(
        "order-detail/<int:order_id>/",
        RedirectView.as_view(
            pattern_name="order_detail", permanent=False, query_string=True
        ),
        name="legacy_order_detail",
    ),
    # Favicon
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/favicon.svg", permanent=False),
        name="favicon",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
