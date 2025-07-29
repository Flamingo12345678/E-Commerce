"""
Vues pour la gestion des paiements YEE E-Commerce
Version nettoyée et corrigée
"""

import stripe
import logging
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone

# Configuration du logger
logger = logging.getLogger(__name__)

# Import des modèles
from .models import PaymentMethod, Transaction
from .payment_services import (
    UnifiedPaymentService,
    PaymentMethodService,
    PaymentProcessingError,
    PayPalPaymentProcessor,
)
from store.models import Order, Cart


@login_required
def payment_options(request):
    """Affiche les options de paiement disponibles."""
    # Récupérer les paramètres de paiement
    amount = request.GET.get("amount", "0.00")
    description = request.GET.get("description", "Commande MyStore")
    source = request.GET.get("source", "unknown")

    # Récupérer le panier actif de l'utilisateur
    cart = Cart.objects.filter(user=request.user).first()

    if not cart:
        orders = Order.objects.none()
    else:
        # Récupérer uniquement les commandes non payées du panier
        orders = (
            cart.orders.filter(ordered=False)
            .select_related("product")
            .order_by("created_at")
        )

    order_items = []
    total_amount = Decimal("0.00")

    # Calculer les totaux pour chaque ligne
    for order in orders:
        item_total = order.product.price * order.quantity
        total_amount += item_total
        order_items.append(
            {
                "product": {
                    "name": order.product.name,
                    "price": order.product.price,
                },
                "quantity": order.quantity,
                "unit_price": order.product.price,
                "item_total": item_total,
                "order": order,
            }
        )

        # Récupérer les méthodes de paiement de l'utilisateur
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    default_method = payment_methods.filter(is_default=True).first()

    # Convertir le montant de l'URL en Decimal si fourni
    try:
        amount_decimal = Decimal(amount.replace(",", "."))
    except (InvalidOperation, TypeError):
        amount_decimal = total_amount

    # Utiliser le total calculé si aucun montant valide n'est fourni
    if amount_decimal <= 0:
        amount_decimal = total_amount

    context = {
        "amount": amount_decimal,
        "total": total_amount,  # Utiliser le total calculé
        "description": description,
        "source": source,
        "orders": orders,
        "order_items": order_items,
        "payment_methods": payment_methods,
        "default_method": default_method,
        "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, "accounts/payment_options.html", context)


@login_required
@require_POST
def create_stripe_payment_intent(request):
    """Crée un PaymentIntent Stripe pour traitement côté client"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Configuration Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Récupérer les commandes du panier
        cart_orders = Order.objects.filter(user=request.user, ordered=False)
        if not cart_orders.exists():
            return JsonResponse({"error": "Panier vide"}, status=400)

        # Calculer le total
        total_amount = sum(
            order.quantity * order.product.price for order in cart_orders
        )
        amount_cents = int(total_amount * 100)  # Stripe utilise les centimes

        # Préparer les métadonnées
        order_ids = ",".join(str(order.id) for order in cart_orders)
        nb_articles = len(cart_orders)

        # Créer le PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="eur",
            metadata={
                "user_id": str(request.user.id),
                "order_ids": order_ids,
                "nb_articles": str(nb_articles),
                "email": request.user.email,
            },
            description=f"Commande YEE E-Commerce - {nb_articles} articles",
            receipt_email=request.user.email,
            automatic_payment_methods={
                "enabled": True,
            },
        )

        logger.info(f"PaymentIntent créé: {intent.id} pour {total_amount}€")

        return JsonResponse(
            {
                "client_secret": intent.client_secret,
                "amount": float(total_amount),
                "currency": "eur",
                "payment_intent_id": intent.id,
            }
        )

    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe lors de la création: {e}")
        return JsonResponse({"error": f"Erreur Stripe: {str(e)}"}, status=500)
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return JsonResponse({"error": f"Erreur système: {str(e)}"}, status=500)


@csrf_exempt
@require_POST
def confirm_stripe_payment(request):
    """Confirme et finalise un paiement Stripe après succès côté client"""
    import json
    import logging
    from decimal import Decimal

    logger = logging.getLogger(__name__)

    try:
        # Configuration Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Parser les données JSON
        data = json.loads(request.body)
        payment_intent_id = data.get("payment_intent_id")

        if not payment_intent_id:
            return JsonResponse({"error": "Payment Intent ID manquant"}, status=400)

        logger.info(f"Confirmation paiement Stripe: {payment_intent_id}")

        # Récupérer le PaymentIntent depuis Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Vérifier le statut
        if payment_intent.status != "succeeded":
            error_msg = f"Paiement non réussi, statut: {payment_intent.status}"
            logger.error(error_msg)
            return JsonResponse({"error": error_msg}, status=400)

        # Récupérer les métadonnées
        user_id = int(payment_intent.metadata.get("user_id"))
        order_ids_str = payment_intent.metadata.get("order_ids")

        if user_id != request.user.id:
            return JsonResponse({"error": "Utilisateur non autorisé"}, status=403)

        # Récupérer les commandes
        order_ids = [
            int(oid.strip())
            for oid in order_ids_str.split(",")
            if oid.strip().isdigit()
        ]
        cart_orders = Order.objects.filter(
            id__in=order_ids, user=request.user, ordered=False
        )

        if not cart_orders.exists():
            return JsonResponse({"error": "Commandes introuvables"}, status=400)

        # Démarrer une transaction atomique
        with db_transaction.atomic():
            # Créer ou récupérer la méthode de paiement
            payment_method, created = PaymentMethod.objects.get_or_create(
                user=request.user,
                provider="stripe",
                defaults={"type": "card", "is_default": False},
            )

            # Créer la transaction
            amount_decimal = Decimal(payment_intent.amount) / 100
            transaction = Transaction.objects.create(
                user=request.user,
                payment_method=payment_method,
                amount=amount_decimal,
                status="succeeded",
                transaction_id=payment_intent.id,
                order_id=order_ids_str,
                provider_response=json.dumps(
                    {
                        "payment_intent_id": payment_intent.id,
                        "amount": payment_intent.amount,
                        "currency": payment_intent.currency,
                        "status": payment_intent.status,
                        "created": payment_intent.created,
                    }
                ),
            )

            # Marquer les commandes comme payées et mettre à jour le stock
            for order in cart_orders:
                order.ordered = True
                order.date_ordered = timezone.now()
                order.save()

                # Diminuer le stock via la variante appropriée
                product = order.product
                if not product.reduce_stock(order.size, order.quantity):
                    logger.warning(
                        f"Stock insuffisant pour {product.name} "
                        f"taille {order.size or 'unique'}, quantité demandée: {order.quantity}"
                    )

            logger.info(f"Commande finalisée - Transaction: {transaction.id}")

            # Préparer l'URL de redirection
            success_url = (
                f"/accounts/payment/success/"
                f"?transaction_id={transaction.id}"
                f"&amount={float(amount_decimal):.2f}"
                f"&method=stripe"
            )

            return JsonResponse(
                {
                    "success": True,
                    "redirect_url": success_url,
                    "transaction_id": transaction.id,
                    "amount": float(amount_decimal),
                }
            )

    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe: {e}")
        return JsonResponse({"error": f"Erreur Stripe: {str(e)}"}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Format JSON invalide"}, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation: {e}", exc_info=True)
        return JsonResponse({"error": f"Erreur système: {str(e)}"}, status=500)


@login_required
@require_POST
def process_paypal_payment(request):
    """Initie un paiement via PayPal"""
    try:
        # Récupérer les commandes du panier
        cart_orders = Order.objects.filter(user=request.user, ordered=False)
        if not cart_orders.exists():
            messages.warning(request, "Votre panier est vide.")
            return redirect("store:cart")

        # Calculer le total
        total = sum(order.quantity * order.product.price for order in cart_orders)

        # Préparer les données de paiement
        order_ids = ",".join(str(order.id) for order in cart_orders)
        nb_articles = len(cart_orders)
        description = f"Commande YEE E-Commerce - {nb_articles} articles"

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
                error_msg = "URL d'approbation PayPal introuvable"
                raise PaymentProcessingError(error_msg)

        else:
            messages.error(request, f"Erreur PayPal: {result['error']}")
            return redirect("accounts:payment_options")

    except Exception as e:
        error_msg = f"Erreur lors de l'initialisation PayPal: {str(e)}"
        messages.error(request, error_msg)
        return redirect("payment_options")


@login_required
@require_GET
def execute_paypal_payment(request):
    """Exécute un paiement PayPal après approbation"""
    try:
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")

        if not payment_id or not payer_id:
            messages.error(request, "Paramètres PayPal manquants")
            return redirect("accounts:payment_options")

        # Récupérer l'ID de transaction depuis la session
        transaction_id = request.session.get("paypal_transaction_id")
        if not transaction_id:
            messages.error(request, "Session PayPal expirée")
            return redirect("accounts:payment_options")

        # Récupérer la transaction
        transaction = Transaction.objects.get(
            transaction_id=transaction_id, user=request.user
        )

        # Exécuter le paiement PayPal
        PayPalPaymentProcessor.execute_payment(payment_id, payer_id)

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
        error_msg = f"Erreur lors de l'exécution PayPal: {str(e)}"
        messages.error(request, error_msg)
        return redirect("payment_options")


def _finalize_successful_payment(request, transaction, cart_orders):
    """Finalise une commande après paiement réussi"""
    try:
        with db_transaction.atomic():
            # Marquer les commandes comme payées
            for order in cart_orders:
                order.ordered = True
                order.date_ordered = timezone.now()
                order.save()

                # Diminuer le stock via la variante appropriée
                product = order.product
                if not product.reduce_stock(order.size, order.quantity):
                    logger.warning(
                        f"Stock insuffisant pour {product.name} "
                        f"taille {order.size or 'unique'}, quantité: {order.quantity}"
                    )

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
        error_msg = f"Erreur lors de la finalisation: {str(e)}"
        messages.error(request, error_msg)
        return redirect("payment_options")


@login_required
def payment_success(request):
    """Page de confirmation de paiement réussi avec redirection vers order detail"""
    # Récupérer les informations de la transaction depuis l'URL
    transaction_id = request.GET.get("transaction_id")
    payment_method = request.GET.get("method", "stripe")
    amount_str = request.GET.get("amount", "0.00")

    # Récupérer la dernière commande payée de l'utilisateur
    from store.models import Order

    latest_order = (
        Order.objects.filter(user=request.user, ordered=True)
        .order_by("-date_ordered")
        .first()
    )

    # Déterminer l'URL de redirection
    if latest_order:
        from django.urls import reverse

        order_url = reverse("store:order_detail", kwargs={"order_id": latest_order.id})
        redirect_url = order_url + "?payment=success"
    else:
        redirect_url = "/accounts/order-history/?payment=success"

    # Si on a un transaction_id, récupérer le montant depuis la base
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
        "redirect_url": redirect_url,
        "latest_order": latest_order,
    }

    return render(request, "accounts/payment_success_notification.html", context)


@login_required
def payment_failed(request):
    """Page de notification de paiement échoué avec redirection vers panier"""
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
        "redirect_delay": 8,  # 8 secondes pour lire l'erreur
        "redirect_url": "/cart/",  # Retour au panier pour réessayer
    }

    return render(request, "accounts/payment_failed_notification.html", context)


@login_required
def payment_cancelled(request):
    """Vue pour les paiements annulés"""
    messages.info(request, "Paiement annulé par l'utilisateur")
    return redirect("accounts:payment_options")


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
    """Ajoute une nouvelle méthode de paiement"""
    try:
        card_number = request.POST.get("card_number", "").replace(" ", "")
        expiry_month = request.POST.get("expiry_month")
        expiry_year = request.POST.get("expiry_year")
        cvv = request.POST.get("cvv")

        # Validation basique
        if len(card_number) < 13 or not expiry_month or not expiry_year or not cvv:
            raise ValidationError("Informations de carte incomplètes")

        # Dans un vrai système, on utiliserait Stripe pour tokeniser
        # Ici on simule avec des données factices
        PaymentMethodService.add_payment_method(
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
    """Supprime une méthode de paiement"""
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
    """Définit une méthode de paiement comme défaut"""
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
@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook pour recevoir les événements Stripe"""
    from .webhook_services import StripeWebhookService

    return StripeWebhookService.process_webhook(request)


@csrf_exempt
@require_POST
def paypal_webhook(request):
    """Webhook pour recevoir les événements PayPal"""
    from .webhook_services import PayPalWebhookService

    return PayPalWebhookService.process_webhook(request)


@login_required
@require_POST
def create_payment_intent(request):
    """Crée un PaymentIntent Stripe pour le paiement côté client"""
    try:
        data = request.POST
        amount_str = data.get("amount", "0")

        # Normaliser le format du montant (remplacer virgule par point)
        amount_str = amount_str.replace(",", ".")
        amount = Decimal(amount_str)

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

    except Exception:
        return JsonResponse({"error": "Format de montant invalide"}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_confirm_payment(request):
    """Confirme le paiement Stripe côté serveur après succès côté client"""
    import json
    import logging
    from store.models import Order
    from decimal import Decimal
    from django.utils import timezone
    from django.db import transaction as db_transaction

    logger = logging.getLogger(__name__)

    try:
        # Parse des données JSON
        data = json.loads(request.body)
        payment_intent_id = data.get("payment_intent_id")

        if not payment_intent_id:
            return JsonResponse({"error": "Payment Intent ID manquant"}, status=400)

        logger.info(f"Confirmation paiement Stripe: {payment_intent_id}")

        # Vérifier le paiement auprès de Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status != "succeeded":
            return JsonResponse(
                {"error": f"Paiement non confirmé: {payment_intent.status}"},
                status=400,
            )

        # Récupérer les commandes du panier
        cart_orders = Order.objects.filter(user=request.user, ordered=False)

        if not cart_orders.exists():
            return JsonResponse({"error": "Aucune commande en attente"}, status=400)

        # Transaction atomique pour finaliser la commande
        with db_transaction.atomic():
            # Créer une méthode de paiement temporaire pour Stripe
            from .models import PaymentMethod, Transaction

            # Pour Stripe, nous créons une méthode de paiement générique
            # car les détails de carte sont gérés côté Stripe
            payment_method, _ = PaymentMethod.objects.get_or_create(
                user=request.user,
                card_type="other",
                last4="0000",  # Placeholder, les vraies infos sont chez Stripe
                defaults={
                    "cardholder_name": f"Stripe - {request.user.username}",
                    "expiry_month": 12,
                    "expiry_year": 2030,
                    "card_number_hash": "stripe_managed",
                },
            )

            # Calculer le montant total
            total_amount = sum(
                order.quantity * order.product.price for order in cart_orders
            )

            # Vérifier que le montant correspond
            stripe_amount = Decimal(payment_intent.amount) / 100
            if abs(stripe_amount - total_amount) > Decimal("0.01"):
                logger.error(
                    f"Montant incohérent: Stripe={stripe_amount}, "
                    f"Commande={total_amount}"
                )
                return JsonResponse(
                    {"error": "Montant de paiement incohérent"}, status=400
                )

            # Créer la transaction
            transaction = Transaction.objects.create(
                user=request.user,
                payment_method=payment_method,
                amount=stripe_amount,
                provider="stripe",
                status="succeeded",
                transaction_id=payment_intent_id,
                order_id=",".join(str(order.id) for order in cart_orders),
                description=f"Paiement Stripe - {len(cart_orders)} articles",
            )

            # Finaliser les commandes
            for order in cart_orders:
                order.ordered = True
                order.date_ordered = timezone.now()
                order.save()

                # Décrémenter le stock via la variante appropriée
                product = order.product
                if not product.reduce_stock(order.size, order.quantity):
                    logger.warning(
                        f"Stock insuffisant pour {product.name} "
                        f"taille {order.size or 'unique'}: demandé={order.quantity}"
                    )

            logger.info(f"Commande finalisée - Transaction: {transaction.id}")

            # Préparer l'URL de redirection
            success_url = (
                f"/accounts/payment/success/"
                f"?transaction_id={transaction.id}"
                f"&amount={float(stripe_amount):.2f}"
                f"&method=stripe"
            )

            return JsonResponse({"success": True, "redirect_url": success_url})

    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe: {str(e)}")
        return JsonResponse({"error": f"Erreur de paiement: {str(e)}"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides"}, status=400)

    except Exception as e:
        logger.error(f"Erreur lors de la confirmation de paiement: {str(e)}")
        return JsonResponse({"error": "Erreur serveur interne"}, status=500)


@require_http_methods(["GET"])
def stripe_payment_status(request, payment_intent_id):
    """Vérifie le statut d'un paiement Stripe"""
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return JsonResponse(
            {
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency,
            }
        )
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_cancel_payment(request):
    """Annule un paiement Stripe en cours"""
    import json

    try:
        data = json.loads(request.body)
        payment_intent_id = data.get("payment_intent_id")

        if not payment_intent_id:
            return JsonResponse({"error": "Payment Intent ID manquant"}, status=400)

        # Annuler le PaymentIntent si possible
        payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)

        return JsonResponse({"success": True, "status": payment_intent.status})

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception:
        return JsonResponse({"error": "Erreur serveur"}, status=500)
