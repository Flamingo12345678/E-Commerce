from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from store.models import Cart, Order, Product
from .performance_utils import measure_performance
import logging

# Configuration du logger pour le debug
logger = logging.getLogger(__name__)

# Create your views here.


@measure_performance
def index(request):
    """
    Landing page de présentation pure - focus sur l'expérience et les catégories.
    """
    from django.db.models import Count, Q, Avg
    from django.core.cache import cache
    from store.models import Category

    # === SECTION LANDING PAGE PRÉSENTATION ===

    # 1. Catégories vedettes pour la navigation principale
    featured_categories = cache.get("featured_categories")
    if featured_categories is None:
        featured_categories_qs = (
            Category.objects.filter(is_featured=True, is_active=True)
            .annotate(
                products_in_stock=Count("product", filter=Q(product__stock__gt=0))
            )
            .order_by("display_order", "name")[:6]
        )
        # Convertir en liste pour éviter les problèmes de sérialisation
        featured_categories = list(featured_categories_qs)
        cache.set("featured_categories", featured_categories, 3600)  # 1h

    # 2. Produits vedettes par section
    hero_products = cache.get("hero_products")
    if hero_products is None:
        hero_products = (
            Product.objects.select_related("category")
            .filter(stock__gt=0, category__is_active=True)
            .annotate(rating_avg=Avg("rating"))
            .order_by("-rating_avg", "-created_at")[:3]
        )
        cache.set("hero_products", hero_products, 1800)  # 30min

    new_arrivals = (
        Product.objects.select_related("category")
        .filter(stock__gt=0, category__is_active=True)
        .order_by("-created_at")[:5]
    )

    trending_products = (
        Product.objects.select_related("category")
        .filter(stock__gt=0, category__is_active=True)
        .order_by("-id")[:5]
    )

    # === STATISTIQUES DE LA BOUTIQUE ===

    shop_stats = cache.get("shop_stats")
    if shop_stats is None:
        shop_stats = {
            "total_products": Product.objects.filter(category__is_active=True).count(),
            "total_categories": Category.objects.filter(is_active=True).count(),
            "products_in_stock": Product.objects.filter(
                stock__gt=0, category__is_active=True
            ).count(),
        }
        cache.set("shop_stats", shop_stats, 3600)  # 1h

    context = {
        # Landing page de présentation
        "featured_categories": featured_categories,
        "hero_products": hero_products,
        "new_arrivals": new_arrivals,
        "trending_products": trending_products,
        "shop_stats": shop_stats,
    }
    return render(request, "store/index.html", context)


# Fonction pour afficher les détails d'un produit
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Récupérer des produits similaires (même catégorie ou produits récents)
    similar_products = Product.objects.exclude(id=product.id).filter(stock__gt=0)

    # Prioriser les produits de la même catégorie
    if product.category:
        similar_products = similar_products.filter(category=product.category)[:5]
    else:
        similar_products = similar_products.order_by("-created_at")[:5]

    context = {"product": product, "similar_products": similar_products}
    return render(request, "store/detail.html", context)


# Fonction pour ajouter un produit au panier
def add_to_cart(request, slug):
    # Vérifier que l'utilisateur est connecté
    if not request.user.is_authenticated:
        messages.warning(
            request, "Vous devez être connecté pour ajouter des produits au panier."
        )
        return redirect("login")

    try:
        with transaction.atomic():
            user = request.user
            product = get_object_or_404(Product, slug=slug)

            # Vérifier le stock disponible avec la fonction utilitaire
            stock_check = check_stock_availability(product, 1)
            if not stock_check["available"]:
                messages.error(request, stock_check["message"])
                return redirect(reverse("product", kwargs={"slug": slug}))

            # Vérifier la quantité déjà dans le panier
            current_cart_quantity = get_user_cart_quantity(user, product)
            total_quantity = current_cart_quantity + 1

            if total_quantity > product.stock:
                messages.warning(
                    request,
                    f"Impossible d'ajouter plus de '{product.name}'. "
                    f"Vous avez déjà {current_cart_quantity} dans votre panier "
                    f"et le stock total est de {product.stock}.",
                )
                return redirect(reverse("product", kwargs={"slug": slug}))

            # Créer ou récupérer le panier
            cart_obj, _ = Cart.objects.get_or_create(user=user)

            # Chercher une commande existante pour ce produit
            existing_order = cart_obj.orders.filter(
                product=product, ordered=False
            ).first()

            if existing_order:
                # Le produit est déjà dans le panier
                if existing_order.quantity >= product.stock:
                    messages.warning(
                        request,
                        f"Vous avez déjà le maximum disponible de "
                        f"'{product.name}' dans votre panier "
                        f"(stock: {product.stock}).",
                    )
                else:
                    # Augmenter la quantité si possible
                    existing_order.quantity += 1
                    existing_order.save()
                    messages.success(
                        request,
                        f"Quantité de '{product.name}' augmentée à "
                        f"{existing_order.quantity}.",
                    )
            else:
                # Créer une nouvelle commande
                order = Order.objects.create(
                    user=user, product=product, quantity=1, ordered=False
                )
                cart_obj.orders.add(order)
                messages.success(
                    request, f"'{product.name}' a été ajouté à votre panier !"
                )

    except Product.DoesNotExist:
        messages.error(request, "Produit introuvable.")
        return redirect("index")
    except Exception as e:
        messages.error(request, "Erreur inattendue lors de l'ajout au panier.")
        # Log pour debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error("Erreur add_to_cart: %s", str(e))
        return redirect(reverse("product", kwargs={"slug": slug}))

    return redirect(reverse("product", kwargs={"slug": slug}))


# Fonction pour afficher le panier
def cart(request):
    # Vérifier que l'utilisateur est connecté
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté pour voir votre panier.")
        return redirect("login")

    # Utiliser la fonction utilitaire optimisée
    cart_data = get_cart_summary(request.user)

    context = {
        "orders": cart_data["orders"],
        "total": cart_data["total_price"],
        "total_items": cart_data["total_items"],
        "is_empty": cart_data["is_empty"],
    }
    return render(request, "store/cart.html", context)


# Fonction pour supprimer le panier
def delete_cart(request):
    if cart := Cart.objects.filter(user=request.user).first():
        cart.delete()
    return redirect("index")


# Fonction pour augmenter la quantité d'un produit dans le panier
def increase_quantity(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    try:
        with transaction.atomic():
            order = get_object_or_404(
                Order, id=order_id, user=request.user, ordered=False
            )

            # Vérifier le stock disponible en temps réel
            product = order.product
            # S'assurer d'avoir les données les plus récentes
            product.refresh_from_db()

            if order.quantity >= product.stock:
                messages.warning(
                    request,
                    f"Stock insuffisant pour '{product.name}'. "
                    f"Stock disponible: {product.stock}, "
                    f"quantité actuelle dans le panier: {order.quantity}",
                )
            else:
                # Vérifier qu'on peut encore ajouter une unité
                if order.quantity + 1 <= product.stock:
                    order.quantity += 1
                    order.save()
                    messages.success(
                        request,
                        f"Quantité de '{product.name}' "
                        f"augmentée à {order.quantity}.",
                    )
                else:
                    messages.warning(
                        request,
                        f"Impossible d'ajouter plus de '{product.name}'. "
                        f"Stock maximum atteint ({product.stock}).",
                    )

    except Order.DoesNotExist:
        messages.error(request, "Produit non trouvé dans votre panier.")
    except Exception as e:
        messages.error(request, "Erreur lors de la modification de la quantité.")
        # Log l'erreur pour debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur increase_quantity: {e}")

    return redirect("cart")


# Fonction pour diminuer la quantité d'un produit dans le panier
def decrease_quantity(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    try:
        order = get_object_or_404(Order, id=order_id, user=request.user, ordered=False)

        if order.quantity > 1:
            order.quantity -= 1
            order.save()
            messages.success(
                request,
                f"Quantité de '{order.product.name}' réduite à {order.quantity}.",
            )
        else:
            # Si quantité = 1, supprimer complètement le produit
            product_name = order.product.name
            cart_obj = Cart.objects.get(user=request.user)
            cart_obj.orders.remove(order)
            order.delete()
            messages.info(request, f"'{product_name}' a été retiré de votre panier.")

    except (Order.DoesNotExist, Cart.DoesNotExist):
        messages.error(request, "Erreur lors de la modification du panier.")

    return redirect("cart")


# Fonction pour supprimer un produit du panier
def remove_from_cart(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    try:
        # Vérifier d'abord si l'ordre existe pour cet utilisateur
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            messages.error(request, "Produit non trouvé dans votre panier.")
            return redirect("cart")

        # Vérifier si l'ordre n'est pas déjà commandé
        if order.ordered:
            message = (
                f"'{order.product.name}' a déjà été commandé et ne peut "
                f"plus être supprimé du panier."
            )
            messages.warning(request, message)
            return redirect("cart")

        product_name = order.product.name
        cart_obj = Cart.objects.get(user=request.user)

        # Supprimer la commande du panier et la supprimer complètement
        cart_obj.orders.remove(order)
        order.delete()

        success_message = f"'{product_name}' a été supprimé de votre panier."
        messages.success(request, success_message)

    except Cart.DoesNotExist:
        messages.error(request, "Erreur lors de la suppression du produit.")

    return redirect("cart")


# Fonction utilitaire pour obtenir les informations du panier
def get_cart_summary(user):
    """
    Retourne un résumé du panier pour un utilisateur donné.
    VERSION OPTIMISÉE avec select_related et prefetch_related.
    """
    if not user.is_authenticated:
        return {"orders": [], "total_items": 0, "total_price": 0, "is_empty": True}

    # Optimisation: récupérer le panier avec une seule requête optimisée
    try:
        cart_obj = (
            Cart.objects.select_related("user")
            .prefetch_related("orders__product")
            .get(user=user)
        )

        # Filtrer les commandes non commandées avec les produits pré-chargés
        orders = cart_obj.orders.filter(ordered=False).select_related("product")

    except Cart.DoesNotExist:
        # Créer un panier vide si n'existe pas
        cart_obj = Cart.objects.create(user=user)
        orders = []

    # Calculs optimisés (les produits sont déjà en mémoire)
    total_items = sum(order.quantity for order in orders)
    total_price = sum(order.quantity * order.product.price for order in orders)

    return {
        "orders": orders,
        "total_items": total_items,
        "total_price": total_price,
        "is_empty": not orders,
        "cart": cart_obj,
    }


# Fonctions utilitaires pour la gestion de stock
def check_stock_availability(product, requested_quantity=1):
    """
    Vérifie la disponibilité du stock pour un produit.

    Args:
        product: Instance du produit à vérifier
        requested_quantity: Quantité demandée (défaut: 1)

    Returns:
        dict: {
            'available': bool,
            'max_quantity': int,
            'message': str
        }
    """
    product.refresh_from_db()  # Données les plus récentes

    if product.stock <= 0:
        return {
            "available": False,
            "max_quantity": 0,
            "message": f"Le produit '{product.name}' n'est plus en stock.",
        }

    if requested_quantity > product.stock:
        return {
            "available": False,
            "max_quantity": product.stock,
            "message": (
                f"Stock insuffisant pour '{product.name}'. "
                f"Stock disponible: {product.stock}"
            ),
        }

    return {
        "available": True,
        "max_quantity": product.stock,
        "message": f"Stock disponible: {product.stock}",
    }


def get_user_cart_quantity(user, product):
    """
    Retourne la quantité d'un produit déjà dans le panier de l'utilisateur.
    VERSION OPTIMISÉE avec select_related.

    Args:
        user: Utilisateur Django
        product: Produit à vérifier

    Returns:
        int: Quantité dans le panier (0 si pas trouvé)
    """
    try:
        # Optimisation: utiliser select_related pour éviter requête extra
        order = (
            Order.objects.select_related("product")
            .filter(user=user, product=product, ordered=False)
            .first()
        )

        return order.quantity if order else 0

    except Exception:
        return 0


# Vue pour le processus de checkout
def checkout(request):
    """
    Vue pour gérer le processus de checkout.
    Affiche le résumé de la commande et traite le paiement.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté pour passer une commande.")
        return redirect("login")

    # Récupérer les données du panier
    cart_data = get_cart_summary(request.user)

    if cart_data["is_empty"]:
        messages.warning(request, "Votre panier est vide.")
        return redirect("cart")

    if request.method == "POST":
        # Validation des informations de livraison
        required_fields = [
            "first_name",
            "last_name",
            "email",
            "address",
            "postal_code",
            "city",
        ]
        for field in required_fields:
            if not request.POST.get(field, "").strip():
                messages.error(request, f"Le champ {field} est requis.")
                return redirect("checkout")

        # Stocker les informations de livraison en session
        request.session["delivery_info"] = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "email": request.POST.get("email"),
            "address": request.POST.get("address"),
            "postal_code": request.POST.get("postal_code"),
            "city": request.POST.get("city"),
        }

        # Rediriger vers les options de paiement avec les paramètres nécessaires
        messages.success(
            request,
            "Informations de livraison enregistrées. Choisissez votre mode de paiement.",
        )

        # Construire l'URL avec les paramètres de paiement
        from urllib.parse import urlencode

        payment_params = {
            "amount": f"{cart_data['total_price']:.2f}".replace(".", ","),
            "description": f"Commande MyStore - {cart_data['total_items']} articles",
            "source": "checkout",
        }
        payment_url = f"/accounts/payment/options/?{urlencode(payment_params)}"
        return redirect(payment_url)

    # Affichage du formulaire de checkout (GET)
    context = {
        "orders": cart_data["orders"],
        "total": cart_data["total_price"],
        "total_items": cart_data["total_items"],
    }
    return render(request, "store/checkout.html", context)


# Vue pour la confirmation de commande
def order_confirmation(request):
    """
    Page de confirmation après une commande réussie.
    """
    return render(request, "store/order_confirmation.html")


# Vue pour l'historique des commandes
def order_history(request):
    """
    Affiche l'historique des commandes de l'utilisateur.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté pour voir vos commandes.")
        return redirect("login")

    # Récupérer les commandes finalisées de l'utilisateur
    orders = (
        Order.objects.filter(user=request.user, ordered=True)
        .select_related("product")
        .order_by("-date_ordered")
    )

    context = {"orders": orders}
    return render(request, "store/order_history.html", context)


# Vue pour voir les détails d'une commande
def order_detail(request, order_id):
    """
    Affiche les détails d'une commande spécifique avec gestion du statut paiement.
    """
    if not request.user.is_authenticated:
        msg = "Vous devez être connecté pour voir cette commande."
        messages.warning(request, msg)
        return redirect("login")

    order = get_object_or_404(Order, id=order_id, user=request.user, ordered=True)

    # Vérifier si on vient d'un paiement réussi
    payment_success = request.GET.get("payment") == "success"
    if payment_success:
        success_msg = (
            f"✅ Paiement confirmé ! Votre commande #{order.id} "
            f"a été traitée avec succès."
        )
        messages.success(request, success_msg)

    context = {
        "order": order,
        "payment_success": payment_success,
        "order_status": "Payé" if order.ordered else "En attente",
    }
    return render(request, "store/order_detail.html", context)


# Vue pour télécharger la facture
def download_invoice(request, order_id):
    """
    Génère et télécharge la facture PDF pour une commande.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    order = get_object_or_404(Order, id=order_id, user=request.user, ordered=True)

    from django.http import HttpResponse

    try:
        # Pour l'instant, on simule un PDF avec du texte
        # Dans une vraie application, utilisez reportlab ou weasyprint
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="facture_{order.id}.pdf"'
        )

        # Contenu simulé de la facture
        invoice_content = f"""
        FACTURE - Commande #{order.id}
        ================================

        Date de commande: {order.date_ordered.strftime('%d/%m/%Y %H:%M')}
        Client: {request.user.get_full_name() or request.user.username}

        Produit: {order.product.name}
        Quantité: {order.quantity}
        Prix unitaire: {order.product.price}€
        Total: {order.total_price}€

        Merci pour votre achat !
        YEE Store
        """

        response.write(invoice_content.encode("utf-8"))
        return response

    except Exception as e:
        messages.error(request, "Erreur lors de la génération de la facture.")
        logger.error(f"Erreur download_invoice: {e}")
        return redirect("order_history")


# Vue pour repasser commande (reorder)
def reorder(request, order_id):
    """
    Recrée une commande basée sur une commande précédente.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    try:
        with transaction.atomic():
            # Récupérer la commande originale
            original_order = get_object_or_404(
                Order, id=order_id, user=request.user, ordered=True
            )

            product = original_order.product
            quantity = original_order.quantity

            # Vérifier la disponibilité du stock
            stock_check = check_stock_availability(product, quantity)
            if not stock_check["available"]:
                messages.error(
                    request,
                    f"Stock insuffisant pour '{product.name}'. "
                    f"Stock disponible: {stock_check['max_quantity']}",
                )
                return redirect("order_history")

            # Vérifier si déjà dans le panier
            current_cart_quantity = get_user_cart_quantity(request.user, product)
            total_quantity = current_cart_quantity + quantity

            if total_quantity > product.stock:
                messages.warning(
                    request,
                    f"Impossible d'ajouter {quantity} '{product.name}'. "
                    f"Vous avez déjà {current_cart_quantity} dans votre panier "
                    f"et le stock total est de {product.stock}.",
                )
                return redirect("order_history")

            # Créer ou récupérer le panier
            cart_obj, _ = Cart.objects.get_or_create(user=request.user)

            # Chercher une commande existante pour ce produit
            existing_order = cart_obj.orders.filter(
                product=product, ordered=False
            ).first()

            if existing_order:
                # Augmenter la quantité
                existing_order.quantity += quantity
                existing_order.save()
                messages.success(
                    request,
                    f"{quantity} '{product.name}' ajouté(s) à votre panier. "
                    f"Quantité totale: {existing_order.quantity}",
                )
            else:
                # Créer une nouvelle commande
                new_order = Order.objects.create(
                    user=request.user, product=product, quantity=quantity, ordered=False
                )
                cart_obj.orders.add(new_order)
                messages.success(
                    request, f"{quantity} '{product.name}' ajouté(s) à votre panier !"
                )

    except Exception as e:
        messages.error(request, "Erreur lors de la repasse de commande.")
        logger.error(f"Erreur reorder: {e}")

    return redirect("cart")


# Vue pour annuler une commande
def cancel_order(request, order_id):
    """
    Annule une commande et remet le stock en place.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    if request.method == "POST":
        try:
            with transaction.atomic():
                order = get_object_or_404(
                    Order, id=order_id, user=request.user, ordered=True
                )

                # Vérifier si la commande peut être annulée
                # (seulement dans les 24h ou si pas encore expédiée)
                time_limit = timezone.now() - timezone.timedelta(hours=24)
                if order.date_ordered < time_limit:
                    messages.error(
                        request,
                        "Cette commande ne peut plus être annulée " "(délai dépassé).",
                    )
                    return redirect("order_history")

                # Remettre le stock
                product = order.product
                product.stock += order.quantity
                product.save()

                # Marquer comme annulée (ou supprimer)
                order.delete()  # Ou ajouter un statut "cancelled" au modèle

                messages.success(
                    request,
                    f"Commande #{order_id} annulée avec succès. "
                    f"Le stock de '{product.name}' a été remis à jour.",
                )

        except Exception as e:
            messages.error(request, "Erreur lors de l'annulation de la commande.")
            logger.error(f"Erreur cancel_order: {e}")

    return redirect("order_history")


# Vue pour les catégories
@measure_performance
def category_view(request, category_slug):
    """
    Page de catégorie avec filtres et pagination.
    """
    from django.db.models import Q, Min, Max
    from django.core.paginator import Paginator
    from store.models import Category

    # Récupérer la catégorie ou 404
    category = get_object_or_404(Category, slug=category_slug)

    # Récupérer les filtres depuis les paramètres GET
    search_query = request.GET.get("q", "")
    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    stock_filter = request.GET.get("stock", "")
    sort_by = request.GET.get("sort", "-created_at")

    # Base queryset optimisée pour cette catégorie
    products_queryset = Product.objects.select_related("category").filter(
        category=category
    )

    # Appliquer les filtres de recherche
    if search_query:
        products_queryset = products_queryset.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Filtres de prix
    if price_min:
        try:
            products_queryset = products_queryset.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if price_max:
        try:
            products_queryset = products_queryset.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # Filtre de stock
    if stock_filter == "in":
        products_queryset = products_queryset.filter(stock__gt=0)
    elif stock_filter == "out":
        products_queryset = products_queryset.filter(stock=0)

    # Tri
    valid_sorts = {
        "name": "name",
        "-name": "-name",
        "price": "price",
        "-price": "-price",
        "created_at": "created_at",
        "-created_at": "-created_at",
        "stock": "stock",
        "-stock": "-stock",
    }

    if sort_by in valid_sorts:
        products_queryset = products_queryset.order_by(valid_sorts[sort_by])
    else:
        products_queryset = products_queryset.order_by("-created_at")

    # Pagination
    paginator = Paginator(products_queryset, 12)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # Statistiques pour la catégorie
    total_products = products_queryset.count()
    in_stock_count = products_queryset.filter(stock__gt=0).count()

    # Prix min/max pour les filtres
    price_range = products_queryset.aggregate(
        min_price=Min("price"), max_price=Max("price")
    )

    context = {
        "category": category,
        "products": products,
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": total_products - in_stock_count,
        "price_range": price_range,
        "search_query": search_query,
        "current_filters": {
            "price_min": price_min,
            "price_max": price_max,
            "stock": stock_filter,
            "sort": sort_by,
        },
        "page_title": f"Catégorie : {category.name}",
    }

    return render(request, "store/category.html", context)
