"""
URLs pour le système de facturation
"""

from django.urls import path
from . import invoice_views

urlpatterns = [
    # URLs pour les clients
    path("invoices/", invoice_views.invoice_list, name="invoice_list"),
    path("invoices/<uuid:uuid>/", invoice_views.invoice_detail, name="invoice_detail"),
    path("invoices/<uuid:uuid>/pay/", invoice_views.invoice_pay, name="invoice_pay"),
    path(
        "invoices/create-from-cart/",
        invoice_views.create_invoice_from_cart,
        name="create_invoice_from_cart",
    ),
    # URLs pour l'administration
    path(
        "admin/invoices/", invoice_views.admin_invoice_list, name="admin_invoice_list"
    ),
    path(
        "admin/invoices/create/",
        invoice_views.admin_create_invoice,
        name="admin_create_invoice",
    ),
    path(
        "admin/invoices/<int:invoice_id>/",
        invoice_views.admin_invoice_detail,
        name="admin_invoice_detail",
    ),
    path(
        "admin/invoices/<int:invoice_id>/send/",
        invoice_views.admin_send_invoice,
        name="admin_send_invoice",
    ),
    path(
        "admin/invoices/dashboard/",
        invoice_views.invoice_dashboard,
        name="invoice_dashboard",
    ),
    # Webhooks
    path(
        "webhooks/stripe/invoices/",
        invoice_views.stripe_webhook_invoice,
        name="stripe_webhook_invoice",
    ),
    path(
        "webhooks/paypal/invoices/",
        invoice_views.paypal_webhook_invoice,
        name="paypal_webhook_invoice",
    ),
]
