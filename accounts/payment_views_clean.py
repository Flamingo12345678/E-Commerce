"""
Vues pour la gestion des paiements YEE E-Commerce
Version nettoyée et corrigée
"""

import stripe
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone

# Import des modèles
from .models import PaymentMethod, Transaction
from .payment_services import (
    UnifiedPaymentService,
    PaymentMethodService,
    PaymentProcessingError,
    PayPalPaymentProcessor,
)
from store.models import Order


@login_required
def payment_options(request):
    """Affiche les options de paiement disponibles."""
    # Récupérer les paramètres de paiement
    amount = request.GET.get("amount", "")
    description = request.GET.get("description", "Commande MyStore")
    source = request.GET.get("source", "unknown")

    # Convertir le montant (format français vers décimal)
    try:
        if amount:
            # Gérer les montants au format français (virgule comme séparateur décimal)
            amount_clean = amount.replace(",", ".").replace(" ", "")
            amount_decimal = Decimal(amount_clean)
        else:
            # Si pas de montant fourni, calculer depuis le panier
            from store.views import get_cart_summary

            cart_data = get_cart_summary(request.user)
            amount_decimal = cart_data.get("total_price", Decimal("0.00"))
    except (ValueError, InvalidOperation):
        # En cas d'erreur, récupérer depuis le panier
        from store.views import get_cart_summary

        cart_data = get_cart_summary(request.user)
        amount_decimal = cart_data.get("total_price", Decimal("0.00"))

    # Récupérer les commandes en cours du panier si source est checkout
    orders = []
    order_items = []
    if source == "checkout":
        orders = Order.objects.filter(user=request.user, ordered=False).select_related(
            "product"
        )

        # Calculer les totaux pour chaque ligne
        for order in orders:
            item_total = order.product.price * order.quantity
            order_items.append(
                {
                    "order": order,
                    "total": item_total,
                }
            )

    # Récupérer les méthodes de paiement de l'utilisateur
    payment_methods = PaymentMethod.objects.filter(user=request.user, is_active=True)
    default_method = payment_methods.filter(is_default=True).first()

    context = {
        "amount": amount_decimal,
        "description": description,
        "source": source,
        "orders": orders,
        "order_items": order_items,
        "payment_methods": payment_methods,
        "default_method": default_method,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
    }

    return render(request, "accounts/payment_options.html", context)


@login_required
@require_POST
def process_stripe_payment(request):
    """
    Traite un paiement via Stripe
    """
    try:
        # Récupérer les données du formulaire
        payment_method_id = request.POST.get("payment_method_id")

        # Récupérer les commandes du panier
        cart_orders = Order.objects.filter(user=request.user, ordered=False)
        if not cart_orders.exists():
            raise ValidationError("Panier vide")

        # Calculer le montant total depuis le panier (plus fiable que le formulaire)
        amount = sum(order.quantity * order.product.price for order in cart_orders)

        if not payment_method_id or amount <= 0:
            raise ValidationError("Données de paiement invalides")

        # Préparer les données de paiement
        order_ids = ",".join(str(order.id) for order in cart_orders)
        description = f"Commande YEE E-Commerce - {len(cart_orders)} articles"

        # Traiter le paiement
        result = UnifiedPaymentService.process_payment(
            user=request.user,
            amount=amount,
            provider="stripe",
            payment_data={"payment_method_id": payment_method_id},
            order_id=order_ids,
            description=description,
        )

        if result["success"]:
            payment_intent = result["provider_data"]

            # Gestion des différents statuts Stripe
            if payment_intent.status == "requires_action":
                return JsonResponse(
                    {
                        "requires_action": True,
                        "payment_intent_client_secret": payment_intent.client_secret,
                    }
                )

            elif payment_intent.status == "succeeded":
                # Paiement réussi immédiatement - finaliser la commande
                return _finalize_successful_payment(
                    request, result["transaction"], cart_orders
                )

            elif payment_intent.status in [
                "requires_confirmation",
                "requires_payment_method",
            ]:
                return JsonResponse(
                    {
                        "requires_action": True,
                        "payment_intent_client_secret": payment_intent.client_secret,
                    }
                )

            elif payment_intent.status == "processing":
                # Paiement en cours - sera finalisé par le webhook
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Paiement en cours de traitement",
                        "redirect_url": f"/accounts/payment/success/?transaction_id={result['transaction'].id}&amount={result['transaction'].amount}&method=stripe",
                    }
                )

            else:
                raise PaymentProcessingError(
                    f"Statut inattendu: {payment_intent.status}"
                )

        else:
            # Redirection vers page d'échec avec notification
            error_url = (
                f"/accounts/payment/failed/"
                f"?error={result['error']}"
                f"&method=stripe"
                f"&amount=0.00"
            )
            return redirect(error_url)

    except Exception as e:
        # Redirection vers page d'échec avec notification
        error_url = (
            f"/accounts/payment/failed/"
            f"?error={str(e)}"
            f"&method=stripe"
            f"&amount=0.00"
        )
        return redirect(error_url)


@login_required
@require_POST
def process_paypal_payment(request):
    """
    Initie un paiement via PayPal
    """
    try:
        # Récupérer les commandes du panier
        cart_orders = Order.objects.filter(user=request.user, ordered=False)
        if not cart_orders.exists():
            messages.warning(request, "Votre panier est vide.")
            return redirect("cart")

        # Calculer le total
        total = sum(order.quantity * order.product.price for order in cart_orders)

        # Préparer les données de paiement
        order_ids = ",".join(str(order.id) for order in cart_orders)
        description = f"Commande YEE E-Commerce - {len(cart_orders)} articles"

        # URLs de retour
        return_url = request.build_absolute_uri("/accounts/payment/paypal/execute/")
        cancel_url = request.build_absolute_uri("/accounts/payment/cancelled/")

        # Traiter le paiement
        result = UnifiedPaymentService.process_payment(
            user=request.user,
            amount=total,
            provider="paypal",
            payment_data={
                "return_url": return_url,
                "cancel_url": cancel_url,
            },
            order_id=order_ids,
            description=description,
        )

        if result["success"]:
            payment = result["provider_data"]
            approval_url = None

            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break

            if approval_url:
                # Stocker l'ID de transaction en session pour l'exécution
                transaction = result["transaction"]
                request.session["paypal_transaction_id"] = transaction.transaction_id

                return redirect(approval_url)
            else:
                raise PaymentProcessingError("URL d'approbation PayPal introuvable")

        else:
            messages.error(request, f"Erreur PayPal: {result['error']}")
            return redirect("payment_options")

    except Exception as e:
        messages.error(request, f"Erreur lors de l'initialisation PayPal: {str(e)}")
        return redirect("payment_options")


@login_required
@require_GET
def execute_paypal_payment(request):
    """
    Exécute un paiement PayPal après approbation
    """
    try:
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")

        if not payment_id or not payer_id:
            messages.error(request, "Paramètres PayPal manquants")
            return redirect("payment_options")

        # Récupérer l'ID de transaction depuis la session
        transaction_id = request.session.get("paypal_transaction_id")
        if not transaction_id:
            messages.error(request, "Session PayPal expirée")
            return redirect("payment_options")

        # Récupérer la transaction
        transaction = Transaction.objects.get(
            transaction_id=transaction_id, user=request.user
        )

        # Exécuter le paiement PayPal
        payment = PayPalPaymentProcessor.execute_payment(payment_id, payer_id)

        # Récupérer les commandes liées à cette transaction
        order_ids = [
            int(oid.strip())
            for oid in transaction.order_id.split(",")
            if oid.strip().isdigit()
        ]
        cart_orders = Order.objects.filter(
            id__in=order_ids, user=request.user, ordered=False
        )

        # Finaliser la commande
        return _finalize_successful_payment(request, transaction, cart_orders)

    except Exception as e:
        messages.error(request, f"Erreur lors de l'exécution PayPal: {str(e)}")
        return redirect("payment_options")


def _finalize_successful_payment(request, transaction, cart_orders):
    """
    Finalise une commande après paiement réussi
    """
    try:
        with db_transaction.atomic():
            # Marquer les commandes comme payées
            for order in cart_orders:
                order.ordered = True
                order.date_ordered = timezone.now()
                order.save()

                # Diminuer le stock
                product = order.product
                if product.stock >= order.quantity:
                    product.stock -= order.quantity
                    product.save()

            # Nettoyer la session PayPal si nécessaire
            if "paypal_transaction_id" in request.session:
                del request.session["paypal_transaction_id"]

            # Redirection vers la page de notification avec les infos
            provider = (
                transaction.payment_method.provider
                if transaction.payment_method
                else "stripe"
            )

            # Formater le montant correctement
            formatted_amount = f"{float(transaction.amount):.2f}"

            success_url = (
                f"/accounts/payment/success/"
                f"?transaction_id={transaction.id}"
                f"&amount={formatted_amount}"
                f"&method={provider}"
            )
            return redirect(success_url)

    except Exception as e:
        messages.error(request, f"Erreur lors de la finalisation: {str(e)}")
        return redirect("payment_options")


@login_required
def payment_success(request):
    """
    Page de confirmation de paiement réussi avec notification et redirection
    """
    # Récupérer les informations de la transaction depuis l'URL
    transaction_id = request.GET.get("transaction_id")
    payment_method = request.GET.get("method", "stripe")
    amount_str = request.GET.get("amount", "0.00")

    # Si on a un transaction_id, récupérer le montant depuis la base de données
    amount_formatted = "0.00"
    if transaction_id:
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
            amount_formatted = f"{float(transaction.amount):.2f}"
        except Transaction.DoesNotExist:
            pass

    # Fallback: utiliser le paramètre URL si pas de transaction trouvée
    if amount_formatted == "0.00" and amount_str != "0.00":
        try:
            amount_decimal = Decimal(amount_str.replace(",", "."))
            amount_formatted = f"{float(amount_decimal):.2f}"
        except (ValueError, InvalidOperation):
            amount_formatted = "0.00"

    context = {
        "transaction_id": transaction_id,
        "payment_method": payment_method,
        "amount": amount_formatted,
        "redirect_delay": 5,  # 5 secondes avant redirection
        "redirect_url": "/accounts/order-history/",  # Historique des commandes
    }

    return render(request, "accounts/payment_success_notification.html", context)


@login_required
def payment_failed(request):
    """
    Page de notification de paiement échoué avec redirection
    """
    # Récupérer les informations de l'erreur depuis l'URL
    error_message = request.GET.get("error", "Paiement refusé")
    payment_method = request.GET.get("method", "stripe")
    amount_str = request.GET.get("amount", "0.00")

    # Formater le montant pour l'affichage
    try:
        amount_decimal = Decimal(amount_str.replace(",", "."))
        amount_formatted = f"{float(amount_decimal):.2f}"
    except (ValueError, InvalidOperation):
        amount_formatted = "0.00"

    context = {
        "error_message": error_message,
        "payment_method": payment_method,
        "amount": amount_formatted,
        "redirect_delay": 10,  # 10 secondes avant redirection
        "redirect_url": "/accounts/payment/options/",
    }

    return render(request, "accounts/payment_failed_notification.html", context)


@login_required
def payment_cancelled(request):
    """Vue pour les paiements annulés"""
    messages.info(request, "Paiement annulé par l'utilisateur")
    return redirect("payment_options")


@login_required
def order_history(request):
    """Affiche l'historique des commandes de l'utilisateur"""
    transactions = Transaction.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "transactions": transactions,
    }

    return render(request, "accounts/order_history.html", context)


@login_required
@require_POST
def add_payment_method(request):
    """
    Ajoute une nouvelle méthode de paiement
    """
    try:
        card_number = request.POST.get("card_number", "").replace(" ", "")
        expiry_month = request.POST.get("expiry_month")
        expiry_year = request.POST.get("expiry_year")
        cvv = request.POST.get("cvv")
        card_name = request.POST.get("card_name", "")

        # Validation basique
        if len(card_number) < 13 or not expiry_month or not expiry_year or not cvv:
            raise ValidationError("Informations de carte incomplètes")

        # Dans un vrai système, on utiliserait Stripe pour tokeniser la carte
        # Ici on simule avec des données factices
        payment_method = PaymentMethodService.add_payment_method(
            user=request.user,
            provider="stripe",
            provider_method_id=f"pm_fake_{card_number[-4:]}",
            card_last4=card_number[-4:],
            card_brand="visa",  # À déterminer depuis le numéro
            card_exp_month=int(expiry_month),
            card_exp_year=int(expiry_year),
        )

        messages.success(request, "Méthode de paiement ajoutée avec succès")

    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")

    return redirect("manage_payment_methods")


@login_required
@require_POST
def remove_payment_method(request, method_id):
    """
    Supprime une méthode de paiement
    """
    try:
        payment_method = get_object_or_404(
            PaymentMethod, id=method_id, user=request.user
        )
        payment_method.delete()
        messages.success(request, "Méthode de paiement supprimée")

    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")

    return redirect("manage_payment_methods")


@login_required
@require_POST
def set_default_payment_method(request, method_id):
    """
    Définit une méthode de paiement comme défaut
    """
    try:
        # Retirer le statut par défaut de toutes les méthodes
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)

        # Définir la nouvelle méthode par défaut
        payment_method = get_object_or_404(
            PaymentMethod, id=method_id, user=request.user
        )
        payment_method.is_default = True
        payment_method.save()

        messages.success(request, "Méthode de paiement par défaut mise à jour.")

    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")

    return redirect("manage_payment_methods")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook pour recevoir les événements Stripe
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Traiter l'événement
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]

        # Trouver la transaction correspondante
        try:
            transaction = Transaction.objects.get(
                provider_transaction_id=payment_intent["id"]
            )

            # Vérifier si cette transaction a déjà été finalisée
            if transaction.status == "succeeded":
                return HttpResponse(status=200)

            # Mettre à jour le statut
            from .payment_services import TransactionService

            TransactionService.update_transaction_status(transaction, "succeeded")

            # Finaliser la commande via le webhook
            from store.models import Order

            # Récupérer les commandes spécifiques à cette transaction
            if transaction.order_id:
                order_ids = [
                    int(oid.strip())
                    for oid in transaction.order_id.split(",")
                    if oid.strip().isdigit()
                ]
                cart_orders = Order.objects.filter(
                    id__in=order_ids, user=transaction.user, ordered=False
                )
            else:
                # Fallback : toutes les commandes non payées de l'utilisateur
                cart_orders = Order.objects.filter(user=transaction.user, ordered=False)

            if cart_orders.exists():
                # Utiliser une transaction atomique pour assurer la cohérence
                with db_transaction.atomic():
                    # Marquer les commandes comme payées
                    for order in cart_orders:
                        order.ordered = True
                        order.date_ordered = timezone.now()
                        order.save()

                        # Diminuer le stock
                        product = order.product
                        if product.stock >= order.quantity:
                            product.stock -= order.quantity
                            product.save()

        except Transaction.DoesNotExist:
            pass

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]

        # Marquer la transaction comme échouée
        try:
            transaction = Transaction.objects.get(
                provider_transaction_id=payment_intent["id"]
            )
            from .payment_services import TransactionService

            TransactionService.update_transaction_status(transaction, "failed")

        except Transaction.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
@require_POST
def create_payment_intent(request):
    """
    Crée un PaymentIntent Stripe pour le paiement côté client
    """
    try:
        data = request.POST
        amount = Decimal(data.get("amount", "0"))

        if amount <= 0:
            raise ValidationError("Montant invalide")

        # Créer le PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe utilise les centimes
            currency="eur",
            metadata={"user_id": request.user.id},
        )

        return JsonResponse(
            {"client_secret": payment_intent.client_secret, "id": payment_intent.id}
        )

    except Exception as e:
        return JsonResponse({"error": "Format de montant invalide"}, status=400)
