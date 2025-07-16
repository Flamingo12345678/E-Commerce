"""
Vues pour le système de facturation
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.conf import settings
import logging
import json
from decimal import Decimal

from .invoice_models import (
    Invoice,
    InvoiceItem,
    InvoicePayment,
    InvoiceTemplate,
    RecurringInvoiceTemplate,
)
from .invoice_services import InvoiceManager
from .models import Shopper
from store.models import Order, Cart

logger = logging.getLogger("payment")


@login_required
def invoice_list(request):
    """
    Liste des factures du client connecté
    """
    invoices = Invoice.objects.filter(customer=request.user).order_by("-created_at")

    # Pagination
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "invoices": page_obj,
        "total_invoices": invoices.count(),
        "paid_invoices": invoices.filter(status="paid").count(),
        "pending_invoices": invoices.filter(status__in=["sent", "overdue"]).count(),
    }

    return render(request, "accounts/invoices/list.html", context)


@login_required
def invoice_detail(request, uuid):
    """
    Détail d'une facture
    """
    invoice = get_object_or_404(Invoice, uuid=uuid, customer=request.user)

    # Marquer comme vue si première fois
    if not invoice.viewed_date:
        invoice.viewed_date = timezone.now()
        invoice.save()

    # Récupérer les liens de paiement
    invoice_manager = InvoiceManager()
    payment_links = invoice_manager.get_payment_links(invoice)

    context = {
        "invoice": invoice,
        "payment_links": payment_links,
        "can_pay": invoice.can_be_paid,
    }

    return render(request, "accounts/invoices/detail.html", context)


@login_required
def invoice_pay(request, uuid):
    """
    Page de paiement d'une facture
    """
    invoice = get_object_or_404(Invoice, uuid=uuid, customer=request.user)

    if not invoice.can_be_paid:
        messages.error(request, "Cette facture ne peut pas être payée.")
        return redirect("invoice_detail", uuid=invoice.uuid)

    # Récupérer les liens de paiement
    invoice_manager = InvoiceManager()
    payment_links = invoice_manager.get_payment_links(invoice)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        if payment_method == "stripe":
            # Rediriger vers Stripe
            if payment_links.get("stripe"):
                return redirect(payment_links["stripe"])
            else:
                messages.error(request, "Erreur lors de la création du lien Stripe.")

        elif payment_method == "paypal":
            # Rediriger vers PayPal
            if payment_links.get("paypal"):
                return redirect(payment_links["paypal"])
            else:
                messages.error(request, "Erreur lors de la création du lien PayPal.")

    context = {
        "invoice": invoice,
        "payment_links": payment_links,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, "accounts/invoices/pay.html", context)


@staff_member_required
def admin_invoice_list(request):
    """
    Liste administrative des factures
    """
    invoices = Invoice.objects.all().order_by("-created_at")

    # Filtres
    status = request.GET.get("status")
    if status:
        invoices = invoices.filter(status=status)

    search = request.GET.get("search")
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search)
            | Q(customer__email__icontains=search)
            | Q(customer__first_name__icontains=search)
            | Q(customer__last_name__icontains=search)
        )

    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistiques
    stats = {
        "total_amount": invoices.aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0"),
        "paid_amount": invoices.filter(status="paid").aggregate(
            total=Sum("total_amount")
        )["total"]
        or Decimal("0"),
        "pending_amount": invoices.filter(status__in=["sent", "overdue"]).aggregate(
            total=Sum("total_amount")
        )["total"]
        or Decimal("0"),
    }

    context = {
        "invoices": page_obj,
        "stats": stats,
        "status_choices": Invoice.INVOICE_STATUS_CHOICES,
        "current_status": status,
        "search_query": search,
    }

    return render(request, "admin/invoices/list.html", context)


@staff_member_required
def admin_create_invoice(request):
    """
    Création d'une nouvelle facture
    """
    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            customer_id = request.POST.get("customer_id")
            customer = get_object_or_404(Shopper, id=customer_id)

            # Créer la facture
            invoice = Invoice.objects.create(
                customer=customer,
                notes=request.POST.get("notes", ""),
            )

            # Ajouter les lignes de facture
            descriptions = request.POST.getlist("description[]")
            quantities = request.POST.getlist("quantity[]")
            unit_prices = request.POST.getlist("unit_price[]")

            for desc, qty, price in zip(descriptions, quantities, unit_prices):
                if desc and qty and price:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=desc,
                        quantity=Decimal(qty),
                        unit_price=Decimal(price),
                    )

            messages.success(
                request, f"Facture {invoice.invoice_number} créée avec succès."
            )
            return redirect("admin_invoice_detail", invoice_id=invoice.id)

        except Exception as e:
            logger.error(f"Erreur lors de la création de la facture: {e}")
            messages.error(request, "Erreur lors de la création de la facture.")

    # Récupérer les clients et templates
    customers = Shopper.objects.filter(is_active=True).order_by("email")
    templates = InvoiceTemplate.objects.all().order_by("name")

    context = {
        "customers": customers,
        "templates": templates,
    }

    return render(request, "admin/invoices/create.html", context)


@staff_member_required
def admin_invoice_detail(request, invoice_id):
    """
    Détail administratif d'une facture
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # Synchroniser le statut avec les fournisseurs
    invoice_manager = InvoiceManager()
    invoice_manager.sync_invoice_status(invoice)

    context = {
        "invoice": invoice,
        "payments": invoice.payments.all().order_by("-created_at"),
    }

    return render(request, "admin/invoices/detail.html", context)


@staff_member_required
@require_http_methods(["POST"])
def admin_send_invoice(request, invoice_id):
    """
    Envoie une facture via les fournisseurs configurés
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    provider = request.POST.get("provider", "stripe")

    if invoice.status != "draft":
        return JsonResponse(
            {
                "success": False,
                "error": "Seules les factures en brouillon peuvent être envoyées.",
            }
        )

    try:
        invoice_manager = InvoiceManager()

        # Créer et envoyer la facture
        if invoice_manager.create_invoice_with_provider(invoice, provider):
            if invoice_manager.send_invoice_with_provider(invoice, provider):
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Facture envoyée via {provider.title()}",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Erreur lors de l'envoi via {provider}",
                    }
                )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Erreur lors de la création via {provider}",
                }
            )

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la facture: {e}")
        return JsonResponse({"success": False, "error": "Erreur interne du serveur"})


@login_required
def create_invoice_from_cart(request):
    """
    Crée une facture à partir du panier actuel
    """
    if request.method == "POST":
        try:
            # Récupérer le panier
            cart = Cart.objects.filter(user=request.user).first()
            if not cart or cart.is_empty:
                messages.error(request, "Votre panier est vide.")
                return redirect("cart")

            # Créer la facture
            invoice = Invoice.objects.create(
                customer=request.user,
                notes=f"Facture générée depuis le panier le {timezone.now().strftime('%d/%m/%Y')}",
            )

            # Ajouter les articles du panier
            for order in cart.orders.filter(ordered=False):
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=order.product,
                    description=f"{order.product.name}",
                    quantity=order.quantity,
                    unit_price=order.product.price,
                )

            messages.success(
                request, f"Facture {invoice.invoice_number} créée avec succès."
            )
            return redirect("invoice_detail", uuid=invoice.uuid)

        except Exception as e:
            logger.error(
                f"Erreur lors de la création de la facture depuis le panier: {e}"
            )
            messages.error(request, "Erreur lors de la création de la facture.")

    return redirect("cart")


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook_invoice(request):
    """
    Webhook pour les événements de facture Stripe
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        import stripe

        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        logger.error("Payload invalide dans le webhook Stripe")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Signature invalide dans le webhook Stripe")
        return HttpResponse(status=400)

    # Traiter l'événement
    if event["type"] == "invoice.paid":
        handle_stripe_invoice_paid(event["data"]["object"])
    elif event["type"] == "invoice.payment_failed":
        handle_stripe_invoice_failed(event["data"]["object"])
    elif event["type"] == "invoice.finalized":
        handle_stripe_invoice_finalized(event["data"]["object"])

    return HttpResponse(status=200)


def handle_stripe_invoice_paid(stripe_invoice):
    """
    Traite le paiement d'une facture Stripe
    """
    try:
        # Trouver notre facture
        invoice = Invoice.objects.get(stripe_invoice_id=stripe_invoice["id"])

        # Créer un enregistrement de paiement
        payment = InvoicePayment.objects.create(
            invoice=invoice,
            amount=Decimal(stripe_invoice["amount_paid"] / 100),
            payment_method="stripe",
            stripe_payment_intent_id=stripe_invoice.get("payment_intent"),
            status="completed",
        )
        payment.mark_as_completed()

        logger.info(f"Paiement Stripe traité pour la facture {invoice.invoice_number}")

    except Invoice.DoesNotExist:
        logger.error(f"Facture Stripe non trouvée: {stripe_invoice['id']}")
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement Stripe: {e}")


def handle_stripe_invoice_failed(stripe_invoice):
    """
    Traite l'échec de paiement d'une facture Stripe
    """
    try:
        invoice = Invoice.objects.get(stripe_invoice_id=stripe_invoice["id"])

        # Créer un enregistrement de paiement échoué
        InvoicePayment.objects.create(
            invoice=invoice,
            amount=Decimal(stripe_invoice["amount_due"] / 100),
            payment_method="stripe",
            stripe_payment_intent_id=stripe_invoice.get("payment_intent"),
            status="failed",
            notes="Paiement échoué via Stripe",
        )

        logger.warning(
            f"Paiement Stripe échoué pour la facture {invoice.invoice_number}"
        )

    except Invoice.DoesNotExist:
        logger.error(f"Facture Stripe non trouvée: {stripe_invoice['id']}")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'échec Stripe: {e}")


def handle_stripe_invoice_finalized(stripe_invoice):
    """
    Traite la finalisation d'une facture Stripe
    """
    try:
        invoice = Invoice.objects.get(stripe_invoice_id=stripe_invoice["id"])
        if invoice.status == "draft":
            invoice.status = "sent"
            invoice.sent_date = timezone.now()
            invoice.save()

        logger.info(f"Facture Stripe finalisée: {invoice.invoice_number}")

    except Invoice.DoesNotExist:
        logger.error(f"Facture Stripe non trouvée: {stripe_invoice['id']}")
    except Exception as e:
        logger.error(f"Erreur lors de la finalisation Stripe: {e}")


@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook_invoice(request):
    """
    Webhook pour les événements de facture PayPal
    """
    try:
        payload = json.loads(request.body)
        event_type = payload.get("event_type")

        if event_type == "INVOICING.INVOICE.PAID":
            handle_paypal_invoice_paid(payload["resource"])
        elif event_type == "INVOICING.INVOICE.CANCELLED":
            handle_paypal_invoice_cancelled(payload["resource"])

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook PayPal: {e}")
        return HttpResponse(status=400)


def handle_paypal_invoice_paid(paypal_invoice):
    """
    Traite le paiement d'une facture PayPal
    """
    try:
        # Trouver notre facture
        invoice = Invoice.objects.get(paypal_invoice_id=paypal_invoice["id"])

        # Créer un enregistrement de paiement
        amount_paid = Decimal(paypal_invoice["payments"]["paid_amount"]["value"])

        payment = InvoicePayment.objects.create(
            invoice=invoice,
            amount=amount_paid,
            payment_method="paypal",
            paypal_payment_id=paypal_invoice.get("payments", {})
            .get("transactions", [{}])[0]
            .get("payment_id"),
            status="completed",
        )
        payment.mark_as_completed()

        logger.info(f"Paiement PayPal traité pour la facture {invoice.invoice_number}")

    except Invoice.DoesNotExist:
        logger.error(f"Facture PayPal non trouvée: {paypal_invoice['id']}")
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement PayPal: {e}")


def handle_paypal_invoice_cancelled(paypal_invoice):
    """
    Traite l'annulation d'une facture PayPal
    """
    try:
        invoice = Invoice.objects.get(paypal_invoice_id=paypal_invoice["id"])
        invoice.status = "cancelled"
        invoice.save()

        logger.info(f"Facture PayPal annulée: {invoice.invoice_number}")

    except Invoice.DoesNotExist:
        logger.error(f"Facture PayPal non trouvée: {paypal_invoice['id']}")
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation PayPal: {e}")


@staff_member_required
def invoice_dashboard(request):
    """
    Tableau de bord des factures pour les administrateurs
    """
    # Statistiques générales
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status="paid").count()
    overdue_invoices = Invoice.objects.filter(status="overdue").count()

    # Montants
    total_amount = Invoice.objects.aggregate(total=Sum("total_amount"))[
        "total"
    ] or Decimal("0")

    paid_amount = Invoice.objects.filter(status="paid").aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0")

    pending_amount = Invoice.objects.filter(status__in=["sent", "overdue"]).aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0")

    # Factures récentes
    recent_invoices = Invoice.objects.order_by("-created_at")[:10]

    # Factures en retard
    overdue_list = Invoice.objects.filter(status="overdue").order_by("due_date")[:5]

    context = {
        "stats": {
            "total_invoices": total_invoices,
            "paid_invoices": paid_invoices,
            "overdue_invoices": overdue_invoices,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "payment_rate": (
                (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
            ),
        },
        "recent_invoices": recent_invoices,
        "overdue_invoices": overdue_list,
    }

    return render(request, "admin/invoices/dashboard.html", context)
