"""
URLs pour le système de facturation natif Stripe/PayPal
"""

from django.urls import path
from . import invoice_views_native as views

app_name = "invoices"

urlpatterns = [
    # URLs client
    path("", views.invoice_list, name="list"),
    path("<uuid:invoice_id>/", views.invoice_detail, name="detail"),
    path("<uuid:invoice_id>/pay/", views.invoice_pay, name="pay"),
    # URLs admin
    path("admin/create/", views.admin_invoice_create, name="admin_create"),
    path("admin/<uuid:invoice_id>/send/", views.admin_send_invoice, name="admin_send"),
    path("admin/sync/", views.admin_sync_invoices, name="admin_sync"),
    path("admin/stats/", views.admin_invoice_stats, name="admin_stats"),
    # Webhooks
    path("webhooks/stripe/", views.stripe_webhook_native, name="stripe_webhook"),
]
