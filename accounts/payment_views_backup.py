"""
Vues pour la gestion des paiements YEE E-Commerce
"""

import json
import stripe
import uuid
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
from store.models import Order

# Import des services de paiement
from .payment_services import (
    UnifiedPaymentService,
    PaymentMethodService,
    StripePaymentProcessor,
    PayPalPaymentProcessor,
    PaymentProcessingError,
)


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
                    "product": order.product,
                    "quantity": order.quantity,
                    "unit_price": order.product.price,
                    "item_total": item_total,
                }
            )

    context = {
        "amount": amount,
        "total": amount_decimal,
        "description": description,
        "source": source,
        "orders": orders,
        "order_items": order_items,
        "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
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
        
        print(f"DEBUG process_stripe_payment: amount calculé depuis panier = {amount}")

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
            print(f"DEBUG: PaymentIntent status = {payment_intent.status}")

            # Si le paiement nécessite une confirmation (3D Secure)
            if payment_intent.status == "requires_action":
                return JsonResponse(
                    {
                        "requires_action": True,
                        "payment_intent_client_secret": payment_intent.client_secret,
                    }
                )

            # Si le paiement est réussi IMMÉDIATEMENT
            elif payment_intent.status == "succeeded":
                print(f"DEBUG: PaymentIntent succeeded IMMÉDIATEMENT")
                return _finalize_successful_payment(
                    request, result["transaction"], cart_orders
                )
                
            # Si le paiement nécessite une confirmation côté client
            elif payment_intent.status in ["requires_confirmation", "requires_payment_method"]:
                print(f"DEBUG: PaymentIntent nécessite confirmation: {payment_intent.status}")
                return JsonResponse(
                    {
                        "requires_action": True,
                        "payment_intent_client_secret": payment_intent.client_secret,
                    }
                )
                
            # Si le paiement est en cours de traitement
            elif payment_intent.status == "processing":
                print(f"DEBUG: PaymentIntent en cours de traitement - webhook va finaliser")
                # Redirection vers une page d'attente ou de confirmation
                return JsonResponse({
                    "success": True,
                    "message": "Paiement en cours de traitement",
                    "redirect_url": f"/accounts/payment/success/?transaction_id={result['transaction'].id}&amount={result['transaction'].amount}&method=stripe"
                })

            else:
                print(f"DEBUG: Statut PaymentIntent inattendu: {payment_intent.status}")
                raise PaymentProcessingError(
                    f"Statut inattendu: {payment_intent.status}"
                )

        else:
            # Redirection vers page d'échec avec notification
            error_url = (
                f"/accounts/payment/failed/"
                f"?error={result['error']}"
                f"&method=stripe"
                f"&amount={amount}"
            )
            return redirect(error_url)

    except Exception as e:
        # Redirection vers page d'échec avec notification
        error_url = (
            f"/accounts/payment/failed/"
            f"?error=Erreur de traitement: {str(e)}"
            f"&method=stripe"
            f"&amount=0.00"
        )
        return redirect(error_url)


@login_required
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

        # Traiter le paiement PayPal
        result = UnifiedPaymentService.process_payment(
            user=request.user,
            amount=total,
            provider="paypal",
            payment_data={"return_url": return_url, "cancel_url": cancel_url},
            order_id=order_ids,
            description=description,
        )

        if result["success"]:
            payment = result["provider_data"]
            transaction = result["transaction"]

            # Debug pour process_paypal_payment
            print(f"PayPal Process Debug:")
            print(f"  transaction_id: {transaction.transaction_id}")
            print(f"  payment links: {[link.rel for link in payment.links]}")

            # Trouver l'URL d'approbation PayPal
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break

            if approval_url:
                # Stocker l'ID de transaction dans la session
                request.session["paypal_transaction_id"] = transaction.transaction_id
                request.session.save()  # Force save
                print(
                    f"  session saved with transaction_id: {transaction.transaction_id}"
                )
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
def execute_paypal_payment(request):
    """
    Exécute le paiement PayPal après approbation de l'utilisateur
    """
    try:
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")
        transaction_id = request.session.get("paypal_transaction_id")

        # Debug détaillé
        print(f"PayPal Execute Debug:")
        print(f"  payment_id: {payment_id}")
        print(f"  payer_id: {payer_id}")
        print(f"  transaction_id: {transaction_id}")
        print(f"  session keys: {list(request.session.keys())}")

        if not payment_id:
            raise ValidationError("ID de paiement PayPal manquant")
        if not payer_id:
            raise ValidationError("ID du payeur PayPal manquant")
        if not transaction_id:
            raise ValidationError("ID de transaction en session manquant")

        # Récupérer la transaction
        transaction = get_object_or_404(
            Transaction, transaction_id=transaction_id, user=request.user
        )

        # Exécuter le paiement PayPal
        payment = PayPalPaymentProcessor.execute_payment(payment_id, payer_id)

        # Mettre à jour la transaction
        from .payment_services import TransactionService

        TransactionService.update_transaction_status(
            transaction, "succeeded", payment_id
        )

        # Finaliser la commande
        order_ids = transaction.order_id.split(",")
        cart_orders = Order.objects.filter(
            id__in=order_ids, user=request.user, ordered=False
        )

        return _finalize_successful_payment(request, transaction, cart_orders)

    except Exception as e:
        messages.error(request, f"Erreur lors de l'exécution PayPal: {str(e)}")
        return redirect("payment_options")


def _finalize_successful_payment(request, transaction, cart_orders):
    """
    Finalise une commande après paiement réussi
    """
    print(f"DEBUG _finalize_successful_payment: DÉBUT de la finalisation")
    print(f"DEBUG: transaction.id = {transaction.id}, amount = {transaction.amount}")
    print(f"DEBUG: cart_orders.count() = {cart_orders.count()}")
    
    try:
        with db_transaction.atomic():
            print(f"DEBUG: Dans la transaction atomique")
            
            # Marquer les commandes comme payées
            orders_updated = 0
            for order in cart_orders:
                print(f"DEBUG: Traitement order {order.id}, product: {order.product.name}")
                order.ordered = True
                order.date_ordered = timezone.now()
                order.save()
                orders_updated += 1

                # Diminuer le stock
                product = order.product
                if product.stock >= order.quantity:
                    old_stock = product.stock
                    product.stock -= order.quantity
                    product.save()
                    print(f"DEBUG: Stock mis à jour {product.name}: {old_stock} -> {product.stock}")
                else:
                    print(f"DEBUG: Stock insuffisant pour {product.name}")
                    
            print(f"DEBUG: {orders_updated} commandes mises à jour")

            # Nettoyer la session
            if "paypal_transaction_id" in request.session:
                del request.session["paypal_transaction_id"]
                print(f"DEBUG: Session PayPal nettoyée")

            # Redirection vers la page de notification avec les infos
            provider = (
                transaction.payment_method.provider
                if transaction.payment_method
                else "stripe"
            )
            # Debug: afficher le montant de la transaction
            print(f"DEBUG _finalize_successful_payment: transaction.amount = {transaction.amount}")
            print(f"DEBUG _finalize_successful_payment: transaction.id = {transaction.id}")
            
            # Formater le montant correctement
            formatted_amount = f"{float(transaction.amount):.2f}"
            print(f"DEBUG _finalize_successful_payment: formatted_amount = {formatted_amount}")
            
            success_url = (
                f"/accounts/payment/success/"
                f"?transaction_id={transaction.id}"
                f"&amount={formatted_amount}"
                f"&method={provider}"
            )
            print(f"DEBUG: Redirection vers {success_url}")
            return redirect(success_url)

    except Exception as e:
        print(f"DEBUG: ERREUR dans _finalize_successful_payment: {str(e)}")
        print(f"DEBUG: Type d'erreur: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f"Erreur lors de la finalisation: {str(e)}")
        return redirect("payment_options")


@login_required
def debug_transactions(request):
    """Vue de debug pour afficher les dernières transactions"""
    transactions = Transaction.objects.filter(user=request.user).order_by("-created_at")[:5]
    
    debug_info = []
    for transaction in transactions:
        debug_info.append({
            "id": transaction.id,
            "transaction_id": transaction.transaction_id,
            "amount": f"{transaction.amount}",
            "status": transaction.status,
            "provider": transaction.provider,
            "description": transaction.description,
            "created_at": transaction.created_at.isoformat(),
        })
    
    return JsonResponse({"transactions": debug_info}, indent=2)


@login_required  
def test_stripe_transaction(request):
    """Vue de test pour créer une transaction Stripe avec montant du panier"""
    # Récupérer les commandes du panier
    cart_orders = Order.objects.filter(user=request.user, ordered=False)
    if not cart_orders.exists():
        return JsonResponse({"error": "Panier vide"}, status=400)
        
    # Calculer le montant total depuis le panier
    amount = sum(order.quantity * order.product.price for order in cart_orders)
    
    # Créer une transaction test avec le montant réel du panier
    transaction = Transaction.objects.create(
        user=request.user,
        order_id="TEST_CART_" + str(uuid.uuid4().hex[:8]),
        transaction_id=f"test_cart_{uuid.uuid4().hex[:12]}",
        provider="stripe",
        amount=amount,  # Montant réel du panier
        description=f"Test paiement panier - {len(cart_orders)} articles",
        status="succeeded",
    )
    
    # Rediriger vers la notification de succès
    formatted_amount = f"{float(transaction.amount):.2f}"
    success_url = (
        f"/accounts/payment/success/"
        f"?transaction_id={transaction.id}"
        f"&amount={formatted_amount}"
        f"&method=stripe"
    )
    return redirect(success_url)


@login_required
def test_full_payment_flow(request):
    """Vue de test qui simule un paiement Stripe complet avec finalisation"""
    from store.models import Order
    
    # Récupérer les commandes du panier
    cart_orders = Order.objects.filter(user=request.user, ordered=False)
    if not cart_orders.exists():
        return JsonResponse({"error": "Panier vide pour le test"}, status=400)
        
    # Calculer le montant total depuis le panier
    amount = sum(order.quantity * order.product.price for order in cart_orders)
    order_ids = ",".join(str(order.id) for order in cart_orders)
    
    print(f"TEST: Début test paiement complet")
    print(f"TEST: {cart_orders.count()} articles dans le panier")
    print(f"TEST: Montant total = {amount}")
    print(f"TEST: Order IDs = {order_ids}")
    
    # Créer une transaction test avec les bonnes données
    transaction = Transaction.objects.create(
        user=request.user,
        order_id=order_ids,  # IDs des commandes spécifiques
        transaction_id=f"test_full_{uuid.uuid4().hex[:12]}",
        provider="stripe",
        amount=amount,  # Montant réel du panier
        description=f"Test paiement complet - {len(cart_orders)} articles",
        status="processing",  # Simuler le workflow Stripe
    )
    
    print(f"TEST: Transaction créée {transaction.id}")
    
    # Simuler la finalisation comme le ferait le webhook
    try:
        print(f"TEST: Simulation finalisation webhook")
        
        # Récupérer les commandes spécifiques à cette transaction
        order_ids_list = [int(oid.strip()) for oid in transaction.order_id.split(",") if oid.strip().isdigit()]
        test_orders = Order.objects.filter(id__in=order_ids_list, user=transaction.user, ordered=False)
        
        if test_orders.exists():
            print(f"TEST: Finalisation {test_orders.count()} commandes")
            
            # Marquer les commandes comme payées
            for order in test_orders:
                print(f"TEST: Finalisation order {order.id} - {order.product.name}")
                order.ordered = True
                order.date_ordered = timezone.now()
                order.save()

                # Diminuer le stock
                product = order.product
                if product.stock >= order.quantity:
                    old_stock = product.stock
                    product.stock -= order.quantity
                    product.save()
                    print(f"TEST: Stock {product.name}: {old_stock} -> {product.stock}")
                    
            # Mettre à jour le statut de la transaction
            transaction.status = "succeeded"
            transaction.save()
            
            print(f"TEST: Finalisation terminée avec succès")
            
        # Rediriger vers la notification de succès
        formatted_amount = f"{float(transaction.amount):.2f}"
        success_url = (
            f"/accounts/payment/success/"
            f"?transaction_id={transaction.id}"
            f"&amount={formatted_amount}"
            f"&method=stripe"
        )
        return redirect(success_url)
        
    except Exception as e:
        print(f"TEST: ERREUR dans la finalisation: {str(e)}")
        return JsonResponse({"error": f"Erreur test: {str(e)}"}, status=500)


@login_required
def debug_cart_status(request):
    """Vue pour vérifier le statut du panier"""
    from store.models import Order
    
    cart_orders = Order.objects.filter(user=request.user, ordered=False)
    paid_orders = Order.objects.filter(user=request.user, ordered=True)
    
    cart_info = []
    for order in cart_orders:
        cart_info.append({
            "id": order.id,
            "product": order.product.name,
            "quantity": order.quantity,
            "price": f"{order.product.price}",
            "total": f"{order.quantity * order.product.price}",
            "ordered": order.ordered,
            "date_ordered": order.date_ordered.isoformat() if order.date_ordered else None
        })
    
    paid_info = []
    for order in paid_orders.order_by("-date_ordered")[:5]:
        paid_info.append({
            "id": order.id,
            "product": order.product.name,
            "quantity": order.quantity,
            "total": f"{order.quantity * order.product.price}",
            "date_ordered": order.date_ordered.isoformat() if order.date_ordered else None
        })
    
    return JsonResponse({
        "cart_orders": cart_info,
        "cart_total": f"{sum(o.quantity * o.product.price for o in cart_orders)}",
        "cart_count": cart_orders.count(),
        "paid_orders": paid_info,
        "paid_count": paid_orders.count()
    }, indent=2)


@login_required
def payment_success(request):
    """
    Page de confirmation de paiement réussi avec notification et redirection
    """
    # Récupérer les informations de la transaction depuis l'URL ou la session
    transaction_id = request.GET.get("transaction_id")
    payment_method = request.GET.get("method", "stripe")
    amount_str = request.GET.get("amount", "0.00")
    
    # Debug: afficher les paramètres reçus
    print(f"DEBUG payment_success: transaction_id={transaction_id}, amount_str={amount_str}, method={payment_method}")
    
    # Si on a un transaction_id, récupérer le montant depuis la base de données
    amount_formatted = "0.00"
    if transaction_id:
        try:
            from .models import Transaction
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
            amount_formatted = f"{float(transaction.amount):.2f}"
            print(f"DEBUG: Transaction trouvée, montant DB = {transaction.amount}")
        except Transaction.DoesNotExist:
            print(f"DEBUG: Transaction {transaction_id} non trouvée")
    
    # Fallback: utiliser le paramètre URL si pas de transaction trouvée
    if amount_formatted == "0.00" and amount_str != "0.00":
        try:
            amount_decimal = Decimal(amount_str.replace(",", "."))
            amount_formatted = f"{float(amount_decimal):.2f}"
            print(f"DEBUG: Utilisation paramètre URL, montant = {amount_formatted}")
        except (ValueError, InvalidOperation):
            print(f"DEBUG: Erreur conversion montant URL: {amount_str}")
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
    Page d'échec de paiement avec notification et redirection
    """
    # Récupérer les informations de l'erreur depuis l'URL ou la session
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
        "redirect_delay": 5,  # 5 secondes avant redirection
        "redirect_url": "/accounts/payment/options/",  # Retour aux options
    }

    return render(request, "accounts/payment_failed_notification.html", context)


@login_required
def payment_cancelled(request):
    """
    Page d'annulation de paiement
    """
    messages.info(request, "Paiement annulé.")
    return render(request, "accounts/payment_cancelled.html")


@login_required
def transaction_history(request):
    """
    Affiche l'historique des transactions de paiement de l'utilisateur
    """
    transactions = Transaction.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "transactions": transactions,
    }

    return render(request, "accounts/transaction_history.html", context)


@login_required
def order_history(request):
    """
    Affiche l'historique des commandes de l'utilisateur
    """
    try:
        from store.models import Order

        orders = (
            Order.objects.filter(user=request.user, ordered=True)
            .select_related("product", "product__category")
            .order_by("-created_at")
        )

        print(f"DEBUG: Found {orders.count()} orders for user {request.user}")

        context = {
            "orders": orders,
        }

        return render(request, "accounts/order_history.html", context)

    except Exception as e:
        print(f"ERROR in order_history: {e}")
        # Retourner une version d'urgence en cas d'erreur
        context = {"orders": [], "error": str(e)}
        return render(request, "accounts/order_history.html", context)


@login_required
@require_POST
def add_payment_method(request):
    """
    Ajoute une nouvelle méthode de paiement
    """
    try:
        card_number = request.POST.get("card_number", "").replace(" ", "")
        cardholder_name = request.POST.get("cardholder_name", "").strip()
        expiry_date = request.POST.get("expiry_date", "").strip()
        cvv = request.POST.get("cvv", "").strip()

        # Parser la date d'expiration
        if "/" not in expiry_date:
            raise ValidationError("Format de date d'expiration invalide")

        month, year = expiry_date.split("/")
        expiry_month = int(month)
        expiry_year = int(f"20{year}")  # Convertir YY en YYYY

        # Ajouter la méthode de paiement
        payment_method = PaymentMethodService.add_payment_method(
            user=request.user,
            card_number=card_number,
            cardholder_name=cardholder_name,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
        )

        messages.success(request, "Méthode de paiement ajoutée avec succès.")

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
        messages.success(request, "Méthode de paiement supprimée.")

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
            from .payment_services import TransactionService

            # Vérifier si cette transaction a déjà été finalisée
            if transaction.status == "succeeded":
                print(f"Webhook: Transaction {transaction.id} déjà finalisée, ignorée")
                return HttpResponse(status=200)

            # Mettre à jour le statut
            TransactionService.update_transaction_status(transaction, "succeeded")
            
            # IMPORTANT: Finaliser la commande (vider le panier, marquer comme payé)
            from store.models import Order
            
            # Récupérer les commandes spécifiques à cette transaction
            if transaction.order_id:
                order_ids = [int(oid.strip()) for oid in transaction.order_id.split(",") if oid.strip().isdigit()]
                cart_orders = Order.objects.filter(id__in=order_ids, user=transaction.user, ordered=False)
            else:
                # Fallback : toutes les commandes non payées de l'utilisateur
                cart_orders = Order.objects.filter(user=transaction.user, ordered=False)
                
            if cart_orders.exists():
                print(f"Webhook: Finalisation {cart_orders.count()} commandes pour transaction {transaction.id}")
                
                # Utiliser une transaction atomique pour assurer la cohérence
                with db_transaction.atomic():
                    # Marquer les commandes comme payées
                    for order in cart_orders:
                        print(f"Webhook: Finalisation order {order.id} - {order.product.name}")
                        order.ordered = True
                        order.date_ordered = timezone.now()
                        order.save()

                        # Diminuer le stock
                        product = order.product
                        if product.stock >= order.quantity:
                            old_stock = product.stock
                            product.stock -= order.quantity
                            product.save()
                            print(f"Webhook: Stock {product.name}: {old_stock} -> {product.stock}")
                        else:
                            print(f"Webhook: Stock insuffisant pour {product.name}")
                            
                print(f"Webhook: Finalisation terminée avec succès")
            else:
                print(f"Webhook: Aucune commande trouvée pour transaction {transaction.id}")
                        
        except Transaction.DoesNotExist:
            print(f"Transaction non trouvée pour PaymentIntent: {payment_intent['id']}")
            pass

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]

        # Marquer la transaction comme échouée
        try:
            transaction = Transaction.objects.get(
                provider_transaction_id=payment_intent["id"]
            )
            from .payment_services import TransactionService

            TransactionService.update_transaction_status(
                transaction,
                "failed",
                error_message=payment_intent.get("last_payment_error", {}).get(
                    "message", ""
                ),
            )
        except Transaction.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
@require_GET
def create_payment_intent(request):
    """
    API pour créer un PaymentIntent Stripe
    """
    try:
        amount_str = request.GET.get("amount", "0")
        # Remplacer la virgule par un point pour la conversion décimale
        amount_str = amount_str.replace(",", ".")
        amount = Decimal(amount_str)

        if amount <= 0:
            return JsonResponse({"error": "Montant invalide"}, status=400)

        # Créer le PaymentIntent
        payment_intent = StripePaymentProcessor.create_payment_intent(
            amount=amount, description="Paiement YEE E-Commerce"
        )

        return JsonResponse(
            {"client_secret": payment_intent.client_secret, "id": payment_intent.id}
        )

    except (InvalidOperation, ValueError) as e:
        print(f"❌ Erreur conversion montant: {e}")
        return JsonResponse({"error": "Format de montant invalide"}, status=400)


@login_required
def test_payment_success(request):
    """Vue de test pour simuler un paiement réussi avec un montant"""
    # Créer une transaction de test avec un montant
    transaction = Transaction.objects.create(
        user=request.user,
        order_id="TEST_ORDER_123",
        transaction_id=f"test_{uuid.uuid4().hex[:12]}",
        provider="stripe",
        amount=Decimal("29.99"),  # Montant de test
        description="Test de paiement - Commande simulée",
        status="succeeded",
    )
    
    # Rediriger vers la notification de succès avec le montant
    formatted_amount = f"{float(transaction.amount):.2f}"
    success_url = (
        f"/accounts/payment/success/"
        f"?transaction_id={transaction.id}"
        f"&amount={formatted_amount}"
        f"&method=stripe"
    )
    return redirect(success_url)
