"""
Vues pour la gestion des factures avec les APIs natives Stripe et PayPal
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q
import json
import stripe
import logging

from .models import Invoice, InvoiceTemplate, RecurringInvoiceTemplate
from .invoice_services_native import UnifiedInvoiceManager, InvoiceServiceError

logger = logging.getLogger(__name__)


@login_required
def invoice_list(request):
    """Liste des factures du client connecté"""
    invoices = Invoice.objects.filter(customer=request.user).order_by("-created_at")

    # Filtrage par statut
    status_filter = request.GET.get("status")
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    # Pagination
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "invoice_statuses": Invoice.STATUS_CHOICES,
    }
    return render(request, "accounts/invoices/list.html", context)


@login_required
def invoice_detail(request, invoice_id):
    """Détail d'une facture"""
    invoice = get_object_or_404(Invoice, id=invoice_id, customer=request.user)

    # Synchroniser le statut avec le fournisseur
    if invoice.provider_invoice_id and invoice.provider == "stripe":
        manager = UnifiedInvoiceManager()
        sync_result = manager.stripe_service.sync_invoice_status(invoice)
        if not sync_result["success"]:
            messages.warning(
                request, "Impossible de synchroniser le statut avec Stripe"
            )

    context = {
        "invoice": invoice,
    }
    return render(request, "accounts/invoices/detail.html", context)


@login_required
def invoice_pay(request, invoice_id):
    """Page de paiement d'une facture"""
    invoice = get_object_or_404(
        Invoice, id=invoice_id, customer=request.user, status__in=["sent", "overdue"]
    )

    # Rediriger vers l'URL de paiement du fournisseur
    if invoice.provider_url:
        return redirect(invoice.provider_url)

    context = {"invoice": invoice, "error": "URL de paiement non disponible"}
    return render(request, "accounts/invoices/pay.html", context)


@staff_member_required
def admin_invoice_create(request):
    """Interface administrative pour créer une facture"""
    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            customer_id = request.POST.get("customer_id")
            provider = request.POST.get("provider", "stripe")
            due_date = request.POST.get("due_date")
            notes = request.POST.get("notes", "")

            # Valider le client
            from .models import Shopper

            customer = get_object_or_404(Shopper, id=customer_id)

            # Créer la facture locale
            invoice = Invoice.objects.create(
                customer=customer,
                provider=provider,
                currency="EUR",
                due_date=due_date if due_date else None,
                notes=notes,
                status="draft",
            )

            # Créer les articles (exemple simple)
            from .models import InvoiceItem

            description = request.POST.get("item_description", "Service")
            quantity = int(request.POST.get("item_quantity", 1))
            unit_price = float(request.POST.get("item_unit_price", 100.00))

            InvoiceItem.objects.create(
                invoice=invoice,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
            )

            # Créer la facture chez le fournisseur
            manager = UnifiedInvoiceManager()
            result = manager.create_invoice(invoice, provider)

            if result["success"]:
                messages.success(
                    request, f"Facture {invoice.invoice_number} créée avec succès"
                )
                return redirect("admin:accounts_invoice_change", invoice.id)
            else:
                messages.error(
                    request,
                    f"Erreur lors de la création: {result.get('error', 'Erreur inconnue')}",
                )

        except Exception as e:
            logger.error(f"Erreur création facture admin: {e}")
            messages.error(request, f"Erreur: {str(e)}")

    # Formulaire de création
    from .models import Shopper

    customers = Shopper.objects.filter(is_active=True).order_by("email")

    context = {
        "customers": customers,
        "providers": [("stripe", "Stripe"), ("paypal", "PayPal")],
    }
    return render(request, "admin/accounts/invoice_create.html", context)


@staff_member_required
@require_http_methods(["POST"])
def admin_send_invoice(request, invoice_id):
    """Envoie une facture depuis l'interface admin"""
    invoice = get_object_or_404(Invoice, id=invoice_id)

    try:
        manager = UnifiedInvoiceManager()
        result = manager.send_invoice(invoice)

        if result["success"]:
            messages.success(
                request, f"Facture {invoice.invoice_number} envoyée avec succès"
            )
        else:
            messages.error(
                request,
                f"Erreur lors de l'envoi: {result.get('error', 'Erreur inconnue')}",
            )

    except Exception as e:
        logger.error(f"Erreur envoi facture admin: {e}")
        messages.error(request, f"Erreur: {str(e)}")

    return redirect("admin:accounts_invoice_change", invoice_id)


@staff_member_required
def admin_sync_invoices(request):
    """Synchronise toutes les factures avec leurs fournisseurs"""
    try:
        manager = UnifiedInvoiceManager()
        manager.sync_all_invoices()

        messages.success(request, "Synchronisation des factures terminée")

    except Exception as e:
        logger.error(f"Erreur sync factures: {e}")
        messages.error(request, f"Erreur: {str(e)}")

    return redirect("admin:accounts_invoice_changelist")


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook_native(request):
    """
    Webhook pour les événements Stripe des factures natives
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    try:
        # Vérifier la signature du webhook
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        logger.error("Payload invalide dans webhook Stripe")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Signature invalide dans webhook Stripe")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    # Traiter l'événement
    try:
        if event["type"] == "invoice.payment_succeeded":
            handle_stripe_invoice_paid(event["data"]["object"])
        elif event["type"] == "invoice.payment_failed":
            handle_stripe_invoice_payment_failed(event["data"]["object"])
        elif event["type"] == "invoice.finalized":
            handle_stripe_invoice_finalized(event["data"]["object"])
        elif event["type"] == "invoice.updated":
            handle_stripe_invoice_updated(event["data"]["object"])
        else:
            logger.info(f"Événement Stripe non traité: {event['type']}")

        return JsonResponse({"status": "success"})

    except Exception as e:
        logger.error(f"Erreur traitement webhook Stripe: {e}")
        return JsonResponse({"error": "Processing error"}, status=500)


def handle_stripe_invoice_paid(stripe_invoice):
    """Traite le paiement d'une facture Stripe"""
    try:
        # Rechercher notre facture locale
        invoice = Invoice.objects.filter(
            provider_invoice_id=stripe_invoice["id"]
        ).first()

        if not invoice:
            logger.warning(
                f"Facture locale non trouvée pour Stripe ID: {stripe_invoice['id']}"
            )
            return

        # Mettre à jour le statut
        invoice.status = "paid"
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=["status", "paid_at"])

        # Créer l'enregistrement de paiement
        from .models import InvoicePayment
        from decimal import Decimal

        InvoicePayment.objects.get_or_create(
            invoice=invoice,
            provider_payment_id=stripe_invoice.get(
                "payment_intent", stripe_invoice["id"]
            ),
            defaults={
                "amount": Decimal(str(stripe_invoice["amount_paid"] / 100)),
                "currency": stripe_invoice["currency"].upper(),
                "provider": "stripe",
                "status": "completed",
                "paid_at": timezone.now(),
                "metadata": {"stripe_invoice": stripe_invoice["id"]},
            },
        )

        logger.info(f"Facture {invoice.invoice_number} marquée comme payée")

    except Exception as e:
        logger.error(f"Erreur traitement paiement Stripe: {e}")


def handle_stripe_invoice_payment_failed(stripe_invoice):
    """Traite l'échec de paiement d'une facture Stripe"""
    try:
        invoice = Invoice.objects.filter(
            provider_invoice_id=stripe_invoice["id"]
        ).first()

        if invoice:
            invoice.status = "overdue"
            invoice.save(update_fields=["status"])
            logger.info(f"Facture {invoice.invoice_number} marquée en retard")

    except Exception as e:
        logger.error(f"Erreur traitement échec paiement Stripe: {e}")


def handle_stripe_invoice_finalized(stripe_invoice):
    """Traite la finalisation d'une facture Stripe"""
    try:
        invoice = Invoice.objects.filter(
            provider_invoice_id=stripe_invoice["id"]
        ).first()

        if invoice:
            # Mettre à jour les URLs si elles ont changé
            invoice.provider_url = stripe_invoice.get(
                "hosted_invoice_url", invoice.provider_url
            )
            invoice.provider_pdf_url = stripe_invoice.get(
                "invoice_pdf", invoice.provider_pdf_url
            )
            invoice.save(update_fields=["provider_url", "provider_pdf_url"])

    except Exception as e:
        logger.error(f"Erreur traitement finalisation Stripe: {e}")


def handle_stripe_invoice_updated(stripe_invoice):
    """Traite la mise à jour d'une facture Stripe"""
    try:
        invoice = Invoice.objects.filter(
            provider_invoice_id=stripe_invoice["id"]
        ).first()

        if invoice:
            # Synchroniser le statut
            status_mapping = {
                "draft": "draft",
                "open": "sent",
                "paid": "paid",
                "uncollectible": "overdue",
                "void": "cancelled",
            }

            new_status = status_mapping.get(stripe_invoice["status"], invoice.status)
            if invoice.status != new_status:
                invoice.status = new_status
                invoice.save(update_fields=["status"])

    except Exception as e:
        logger.error(f"Erreur traitement mise à jour Stripe: {e}")


@staff_member_required
def admin_invoice_stats(request):
    """Statistiques des factures pour l'admin"""
    from django.db.models import Sum, Count, Q
    from datetime import datetime, timedelta

    # Statistiques générales
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status="paid").count()
    overdue_invoices = Invoice.objects.filter(status="overdue").count()

    # Revenus du mois
    this_month = timezone.now().replace(day=1)
    monthly_revenue = (
        Invoice.objects.filter(status="paid", paid_at__gte=this_month).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    # Répartition par fournisseur
    stripe_count = Invoice.objects.filter(provider="stripe").count()
    paypal_count = Invoice.objects.filter(provider="paypal").count()

    context = {
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "overdue_invoices": overdue_invoices,
        "monthly_revenue": monthly_revenue,
        "stripe_count": stripe_count,
        "paypal_count": paypal_count,
        "payment_rate": (
            (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
        ),
    }

    return render(request, "admin/accounts/invoice_stats.html", context)
