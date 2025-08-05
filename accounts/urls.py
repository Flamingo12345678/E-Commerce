from django.urls import path, include
from . import views
from . import payment_views
from . import admin_views
# from . import debug_webhook
from . import firebase_views
from . import views_firebase_unified

app_name = "accounts"

urlpatterns = [
    # URLs unifiées (nouvelles)
    path("auth/", views_firebase_unified.UnifiedAuthView.as_view(), name="unified_auth"),
    path("auth/signup/", views_firebase_unified.UnifiedSignupView.as_view(), name="unified_signup"),
    path("auth/logout/", views_firebase_unified.unified_logout, name="unified_logout"),
    path("auth/profile/", views_firebase_unified.unified_profile, name="unified_profile"),
    path("auth/status/", views_firebase_unified.check_auth_status, name="auth_status"),
    path("auth/link-accounts/", views_firebase_unified.link_accounts, name="link_accounts"),

    # URLs Django traditionnelles (maintenues pour compatibilité)
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("change-password/", views.change_password, name="change_password"),
    # URLs pour la réinitialisation de mot de passe
    path("password-reset/", views.password_reset_request, name="password_reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    # Nouvelles URLs pour les actions du profil
    path("export-data/", views.export_user_data, name="export_user_data"),
    path("delete-account/", views.delete_user_account, name="delete_user_account"),
    path("manage-addresses/", views.manage_addresses, name="manage_addresses"),
    path(
        "manage-payment-methods/",
        views.manage_payment_methods,
        name="manage_payment_methods",
    ),
    path(
        "update-notifications/", views.update_notifications, name="update_notifications"
    ),
    path("setup-two-factor/", views.setup_two_factor, name="setup_two_factor"),
    path("two-factor-qr/", views.two_factor_qr, name="two_factor_qr"),
    path(
        "connect-social/", views.connect_social_account, name="connect_social_account"
    ),
    path("profile-edit-modal/", views.profile_edit_modal, name="profile_edit_modal"),
    
    # Firebase URLs
    path("firebase/", firebase_views.FirebaseAuthView.as_view(), name="firebase_auth"),
    path("firebase/login/", firebase_views.FirebaseAuthView.as_view(), name="firebase_login"),
    path("firebase/logout/", firebase_views.firebase_logout, name="firebase_logout"),
    path("firebase/verify-token/", firebase_views.verify_token_view, name="verify_token"),
    path("firebase/profile/", firebase_views.firebase_profile, name="firebase_profile"),
    path("firebase/link-account/", firebase_views.link_firebase_account, name="link_firebase_account"),
    path("firebase/auth-status/", firebase_views.firebase_auth_status, name="firebase_auth_status"),
    path("firebase/config/", firebase_views.firebase_config_view, name="firebase_config"),
    path("firebase/callback/", firebase_views.SocialAuthCallbackView.as_view(), name="social_auth_callback"),

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
    # path(
    #     "payment/stripe/debug-webhook/",
    #     debug_webhook.debug_stripe_webhook,
    #     name="debug_stripe_webhook",
    # ),
    path(
        "payment/paypal/webhook/",
        payment_views.paypal_webhook,
        name="paypal_webhook",
    ),
    # Pages de résultat
    path("payment/success/", payment_views.payment_success, name="payment_success"),
    path("payment/failed/", payment_views.payment_failed, name="payment_failed"),
    path(
        "payment/cancelled/", payment_views.payment_cancelled, name="payment_cancelled"
    ),
    # Gestion des méthodes de paiement
    path(
        "payment-methods/add/",
        payment_views.add_payment_method,
        name="add_payment_method",
    ),
    path(
        "payment-methods/<int:method_id>/remove/",
        payment_views.remove_payment_method,
        name="remove_payment_method",
    ),
    path(
        "payment-methods/<int:method_id>/default/",
        payment_views.set_default_payment_method,
        name="set_default_payment_method",
    ),
    # Historique des commandes
    path("order-history/", payment_views.order_history, name="order_history"),
    # === FACTURATION ===
    path("", include("accounts.invoice_urls")),
    # === ADMIN DASHBOARDS ===
    path(
        "admin-dashboard/payments/",
        admin_views.payments_dashboard,
        name="payments_dashboard",
    ),
    path(
        "admin-dashboard/webhook-analytics/",
        admin_views.webhook_analytics,
        name="webhook_analytics",
    ),
    path(
        "admin-dashboard/transaction-analytics/",
        admin_views.transaction_analytics,
        name="transaction_analytics",
    ),
]
