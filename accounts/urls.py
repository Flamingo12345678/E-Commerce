from django.urls import path, include
from . import views
from . import payment_views
from .allauth_views import (
    CustomSignupView,
    CustomLoginView,
    profile,
    profile_edit,
    change_password,
    export_user_data,
    delete_user_account,
    manage_addresses,
    manage_payment_methods,
    update_notifications,
    setup_two_factor,
    two_factor_qr
)

app_name = "accounts"

urlpatterns = [
    # URLs personnalisées pour remplacer Allauth - PRIORITAIRES
    path("password/reset/", views.password_reset_request, name="password_reset"),
    path("password-reset-request/", views.password_reset_request, name="password_reset_request"),
    path("password-reset-confirm/<uidb64>/<token>/", views.password_reset_confirm, name="password_reset_confirm"),

    # URLs personnalisées pour le profil et fonctionnalités avancées
    path("profile/", profile, name="profile"),
    path("profile/edit/", profile_edit, name="profile_edit"),
    path("change-password/", change_password, name="change_password"),

    # URLs pour les actions du profil
    path("export-data/", export_user_data, name="export_user_data"),
    path("delete-account/", delete_user_account, name="delete_user_account"),
    path("manage-addresses/", manage_addresses, name="manage_addresses"),
    path(
        "manage-payment-methods/",
        manage_payment_methods,
        name="manage_payment_methods",
    ),
    path(
        "update-notifications/", update_notifications, name="update_notifications"
    ),
    path("setup-two-factor/", setup_two_factor, name="setup_two_factor"),
    path("two-factor-qr/", two_factor_qr, name="two_factor_qr"),

    # URLs de paiement
    path("payment/options/", payment_views.payment_options, name="payment_options"),
    # PayPal
    path(
        "payment/paypal/process/",
        payment_views.process_paypal_payment,
        name="process_paypal_payment",
    ),
    path(
        "payment/paypal/execute/",
        payment_views.execute_paypal_payment,
        name="execute_paypal_payment",
    ),
    # Stripe
    path(
        "payment/stripe/create-intent/",
        payment_views.create_stripe_payment_intent,
        name="create_stripe_payment_intent",
    ),
    path(
        "payment/stripe/confirm/",
        payment_views.confirm_stripe_payment,
        name="stripe_confirm_payment",
    ),
    path(
        "payment/stripe/status/<str:payment_intent_id>/",
        payment_views.stripe_payment_status,
        name="stripe_payment_status",
    ),
    path(
        "payment/stripe/cancel/",
        payment_views.stripe_cancel_payment,
        name="stripe_cancel_payment",
    ),
    path(
        "payment/stripe/webhook/",
        payment_views.stripe_webhook,
        name="stripe_webhook",
    ),

    # URLs de paiement - Success/Cancel/Error
    path("payment/success/", payment_views.payment_success, name="payment_success"),
    path("payment/cancelled/", payment_views.payment_cancelled, name="payment_cancelled"),
    path("payment/failed/", payment_views.payment_failed, name="payment_failed"),
]
