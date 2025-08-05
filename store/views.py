from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from store.models import Cart, Order, Product, Wishlist
from .performance_utils import measure_performance
import logging
from accounts.email_services import EmailService

# Configuration du logger pour le debug
logger = logging.getLogger(__name__)

# Create your views here.


@measure_performance
def product_list(request):
    """
    Vue principale de la boutique - tous les produits avec filtres avancés.
    Remplace les pages de catégories séparées pour une navigation unifiée.
    """
    from django.db.models import Q, Min, Max
    from store.models import Category

    # Récupérer tous les filtres depuis les paramètres GET
    search_query = request.GET.get("q", "")
    category_slug = request.GET.get("category", "")
    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    stock_filter = request.GET.get("stock", "")
    sort_by = request.GET.get("sort", "-created_at")

    # Base queryset optimisée
    products_queryset = Product.objects.select_related("category")

    # Filtrage par catégorie si spécifié
    selected_category = None
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug)
            products_queryset = products_queryset.filter(category=selected_category)
        except Category.DoesNotExist:
            pass

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
        products_queryset = products_queryset.filter(variants__stock__gt=0).distinct()
    elif stock_filter == "out":
        products_queryset = products_queryset.exclude(variants__stock__gt=0)

    # Tri
    valid_sorts = {
        "name": "name",
        "-name": "-name",
        "price": "price",
        "-price": "-price",
        "created_at": "created_at",
        "-created_at": "-created_at",
        "stock": "variants__stock",
        "-stock": "-variants__stock",
    }

    if sort_by in valid_sorts:
        products_queryset = products_queryset.order_by(valid_sorts[sort_by])
    else:
        products_queryset = products_queryset.order_by("-created_at")

    # Pagination
    paginator = Paginator(products_queryset, 12)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # Statistiques pour les filtres
    total_products = products_queryset.count()
    in_stock_count = products_queryset.filter(variants__stock__gt=0).distinct().count()

    # Prix min/max pour les curseurs de prix
    price_range = products_queryset.aggregate(
        min_price=Min("price"), max_price=Max("price")
    )

    # Récupérer toutes les catégories pour le menu de filtres
    all_categories = Category.objects.filter(is_active=True).order_by("name")

    context = {
        "products": products,
        "search_query": search_query,
        "selected_category": selected_category,
        "category_slug": category_slug,
        "all_categories": all_categories,
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": total_products - in_stock_count,
        "price_range": price_range,
        "current_filters": {
            "price_min": price_min,
            "price_max": price_max,
            "stock": stock_filter,
            "sort": sort_by,
        },
        "page_title": (
            f"Catégorie : {selected_category.name}"
            if selected_category
            else "Tous les produits"
        ),
    }

    return render(request, "store/product_list.html", context)


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
                # Temporairement : compter tous les produits
                products_in_stock=Count("product")
            )
            .order_by("display_order", "name")[:6]
        )
        # Convertir en liste pour éviter les problèmes de sérialisation
        featured_categories = list(featured_categories_qs)
        cache.set("featured_categories", featured_categories, 3600)  # 1h

    # 2. Produits vedettes - récupérer plus de produits pour la grille
    hero_products = cache.get("hero_products")
    if hero_products is None:
        # Récupérer 20 produits pour remplir toute la grille
        hero_products = (
            Product.objects.select_related("category")
            .filter(category__is_active=True)
            .annotate(rating_avg=Avg("rating"))
            .order_by("-rating_avg", "-created_at")[:20]
        )
        cache.set("hero_products", hero_products, 1800)  # 30min

    # 3. Produits par catégorie pour diversité
    products_by_category = cache.get("products_by_category")
    if products_by_category is None:
        products_by_category = {}
        categories = Category.objects.filter(is_active=True)[:6]
        for category in categories:
            products_by_category[category.slug] = (
                Product.objects.select_related("category")
                .filter(category=category)
                .order_by("-created_at")[:5]
            )
        cache.set("products_by_category", products_by_category, 1800)

    # 4. Nouveautés et tendances
    new_arrivals = (
        Product.objects.select_related("category")
        .filter(category__is_active=True)
        .order_by("-created_at")[:8]
    )

    trending_products = (
        Product.objects.select_related("category")
        .filter(category__is_active=True)
        .order_by("-id")[:8]
    )

    # === STATISTIQUES DE LA BOUTIQUE ===

    shop_stats = cache.get("shop_stats")
    if shop_stats is None:
        shop_stats = {
            "total_products": Product.objects.filter(category__is_active=True).count(),
            "total_categories": Category.objects.filter(is_active=True).count(),
            # Temporairement : tous les produits considérés en stock
            "products_in_stock": Product.objects.filter(
                category__is_active=True
            ).count(),
        }
        cache.set("shop_stats", shop_stats, 3600)  # 1h

    context = {
        # Landing page de présentation
        "featured_categories": featured_categories,
        "hero_products": hero_products,
        "new_arrivals": new_arrivals,
        "trending_products": trending_products,
        "products_by_category": products_by_category,
        "shop_stats": shop_stats,
    }
    return render(request, "store/index.html", context)


# Fonction pour afficher les détails d'un produit
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Récupérer toutes les variantes disponibles pour ce produit
    variants = product.variants.all().order_by("size")
    available_variants = variants.filter(stock__gt=0)

    # Sélectionner la première variante disponible par défaut
    selected_variant = available_variants.first()

    # Récupérer des produits similaires (même catégorie ou produits récents)
    similar_products = (
        Product.objects.exclude(id=product.id).filter(variants__stock__gt=0).distinct()
    )

    # Prioriser les produits de la même catégorie
    if product.category:
        similar_products = similar_products.filter(category=product.category)[:5]
    else:
        similar_products = similar_products.order_by("-created_at")[:5]

    context = {
        "product": product,
        "variants": variants,
        "available_variants": available_variants,
        "similar_products": similar_products,
        "selected_variant": selected_variant,
    }
    return render(request, "store/product_detail.html", context)


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

            # Récupérer la taille depuis le formulaire si elle existe
            selected_size = (
                request.POST.get("size")
                if request.method == "POST"
                else request.GET.get("size")
            )
            quantity_requested = int(
                request.POST.get("quantity", 1)
                if request.method == "POST"
                else request.GET.get("quantity", 1)
            )

            # Vérifier qu'une taille a été sélectionnée si le produit a des variants
            if product.variants.exists() and not selected_size:
                messages.error(request, "Veuillez sélectionner une taille.")
                return redirect(reverse("store:product_detail", kwargs={"slug": slug}))

            # Vérifier le stock de la variante si une taille est sélectionnée
            if selected_size and product.variants.exists():
                try:
                    from store.models import ProductVariant

                    variant = product.variants.get(size=selected_size)
                    if variant.stock < quantity_requested:
                        messages.error(
                            request,
                            f"Stock insuffisant pour la taille {selected_size}. "
                            f"Seulement {variant.stock} disponible(s).",
                        )
                        return redirect(
                            reverse("store:product_detail", kwargs={"slug": slug})
                        )
                except ProductVariant.DoesNotExist:
                    messages.error(request, f"Taille {selected_size} non disponible.")
                    return redirect(
                        reverse("store:product_detail", kwargs={"slug": slug})
                    )

            # Vérifier que le produit a des variantes en stock
            if not product.is_available:
                messages.error(request, f"'{product.name}' n'est plus disponible.")
                return redirect(reverse("store:product_detail", kwargs={"slug": slug}))

            # Créer ou récupérer le panier
            cart_obj, _ = Cart.objects.get_or_create(user=user)

            # Chercher une commande existante pour ce produit ET cette taille
            existing_order = cart_obj.orders.filter(
                product=product, ordered=False, size=selected_size or ""
            ).first()

            if existing_order:
                # Le produit est déjà dans le panier - augmenter la quantité
                # Vérifier d'abord que nous ne dépassons pas le stock
                new_quantity = existing_order.quantity + quantity_requested

                if selected_size and product.variants.exists():
                    variant = product.variants.get(size=selected_size)
                    if new_quantity > variant.stock:
                        messages.warning(
                            request,
                            f"Impossible d'ajouter {quantity_requested} article(s). "
                            f"Stock maximum pour la taille {selected_size}: {variant.stock}. "
                            f"Vous en avez déjà {existing_order.quantity} dans votre panier.",
                        )
                        return redirect(
                            reverse("store:product_detail", kwargs={"slug": slug})
                        )

                existing_order.quantity = new_quantity
                existing_order.save()
                messages.success(
                    request,
                    f"Quantité de '{product.name}' (taille {selected_size or 'standard'}) "
                    f"augmentée à {existing_order.quantity}.",
                )
            else:
                # Créer une nouvelle commande avec la taille
                order = Order.objects.create(
                    user=user,
                    product=product,
                    quantity=quantity_requested,
                    size=selected_size or "",
                    ordered=False,
                )
                cart_obj.orders.add(order)
                size_msg = f" (taille {selected_size})" if selected_size else ""
                messages.success(
                    request, f"'{product.name}'{size_msg} a été ajouté à votre panier !"
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
        return redirect(reverse("store:product_detail", kwargs={"slug": slug}))

    return redirect(reverse("store:product_detail", kwargs={"slug": slug}))


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

    return redirect("store:cart")


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

    return redirect("store:cart")


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
def check_stock_availability(product, requested_quantity=1, size=None):
    """
    Vérifie la disponibilité du stock pour un produit avec le système de variantes.

    Args:
        product: Instance du produit à vérifier
        requested_quantity: Quantité demandée (défaut: 1)
        size: Taille spécifique (optionnel)

    Returns:
        dict: {
            'available': bool,
            'max_quantity': int,
            'message': str
        }
    """
    product.refresh_from_db()  # Données les plus récentes

    # Utiliser le système de variantes
    if size:
        # Vérifier une taille spécifique
        variant = product.get_variant_by_size(size)
        if not variant:
            return {
                "available": False,
                "max_quantity": 0,
                "message": f"Taille '{size}' non disponible pour '{product.name}'.",
            }

        available_stock = variant.stock
        stock_message = f"Stock disponible pour la taille {size}: {available_stock}"
    else:
        # Vérifier le stock total de toutes les variantes
        if hasattr(product, 'total_stock'):
            available_stock = product.total_stock
        else:
            # Fallback si la propriété n'existe pas
            available_stock = sum(variant.stock for variant in product.variants.all())

        stock_message = f"Stock total disponible: {available_stock}"

    if available_stock <= 0:
        return {
            "available": False,
            "max_quantity": 0,
            "message": f"Le produit '{product.name}' n'est plus en stock.",
        }

    if requested_quantity > available_stock:
        return {
            "available": False,
            "max_quantity": available_stock,
            "message": (
                f"Stock insuffisant pour '{product.name}'. "
                f"{stock_message}"
            ),
        }

    return {
        "available": True,
        "max_quantity": available_stock,
        "message": stock_message,
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
        return redirect("accounts:order_history")


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
            size = getattr(original_order, 'size', None)  # Récupérer la taille si elle existe

            # Vérifier la disponibilité du stock
            stock_check = check_stock_availability(product, quantity, size)
            if not stock_check["available"]:
                messages.error(
                    request,
                    f"Stock insuffisant pour '{product.name}'. "
                    f"Stock disponible: {stock_check['max_quantity']}",
                )
                return redirect("accounts:order_history")

            # Vérifier si déjà dans le panier
            current_cart_quantity = get_user_cart_quantity(request.user, product)
            total_quantity = current_cart_quantity + quantity

            # Utiliser le stock total du produit via ses variantes
            max_stock = product.total_stock if hasattr(product, 'total_stock') else 0
            if size:
                # Si une taille spécifique, vérifier le stock de cette variante
                variant = product.get_variant_by_size(size)
                max_stock = variant.stock if variant else 0

            if total_quantity > max_stock:
                messages.warning(
                    request,
                    f"Impossible d'ajouter {quantity} '{product.name}'. "
                    f"Vous avez déjà {current_cart_quantity} dans votre panier "
                    f"et le stock total est de {max_stock}.",
                )
                return redirect("accounts:order_history")

            # Créer ou récupérer le panier
            cart_obj, _ = Cart.objects.get_or_create(user=request.user)

            # Chercher une commande existante pour ce produit avec la même taille
            existing_order_filter = {'product': product, 'ordered': False}
            if size:
                existing_order_filter['size'] = size

            existing_order = cart_obj.orders.filter(**existing_order_filter).first()

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
                order_data = {
                    'user': request.user,
                    'product': product,
                    'quantity': quantity,
                    'ordered': False
                }
                if size:
                    order_data['size'] = size

                new_order = Order.objects.create(**order_data)
                cart_obj.orders.add(new_order)
                messages.success(
                    request, f"{quantity} '{product.name}' ajouté(s) à votre panier !"
                )

    except Exception as e:
        messages.error(request, "Erreur lors de la repasse de commande.")
        logger.error(f"Erreur reorder: {e}")

    return redirect("store:cart")


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
                    return redirect("accounts:order_history")

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

    return redirect("accounts:order_history")


# Vue pour les catégories - redirection vers la boutique principale
def category_view(request, category_slug):
    """
    Redirection vers la page boutique principale avec filtre de catégorie.
    Simplifie la navigation en évitant les pages séparées.
    """
    from urllib.parse import urlencode

    # Conserver tous les paramètres existants et ajouter la catégorie
    query_params = request.GET.copy()
    query_params["category"] = category_slug

    # Rediriger vers la boutique principale avec les paramètres
    redirect_url = f"/store/?{urlencode(query_params)}"
    return redirect(redirect_url)


# Vues pour la gestion de la wishlist
@require_http_methods(["POST"])
def add_to_wishlist(request):
    """Ajouter un produit à la liste de souhaits"""
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "success": False,
                "message": "Vous devez être connecté pour ajouter à votre liste de souhaits",
            }
        )

    try:
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        # Vérifier si le produit est déjà dans la wishlist
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, product=product
        )

        if created:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"{product.name} ajouté à votre liste de souhaits",
                    "in_wishlist": True,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"{product.name} est déjà dans votre liste de souhaits",
                    "in_wishlist": True,
                }
            )

    except Exception as e:
        logger.error(f"Erreur add_to_wishlist: {e}")
        return JsonResponse(
            {
                "success": False,
                "message": "Erreur lors de l'ajout à la liste de souhaits",
            }
        )


@require_http_methods(["POST"])
def remove_from_wishlist(request):
    """Retirer un produit de la liste de souhaits"""
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour gérer votre liste de souhaits")
        return redirect('accounts:login')

    try:
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        # Supprimer de la wishlist
        deleted_count, _ = Wishlist.objects.filter(
            user=request.user, product=product
        ).delete()

        if deleted_count > 0:
            # Utiliser un nom de produit plus propre
            product_name = product.name

            # Détection améliorée des noms de fichiers ou noms générés automatiquement
            suspicious_patterns = [
                'unsplash', 'jpg', 'png', 'jpeg', '.', '_',
                'cktj', 'tgrks', 'cv', 'wl', 'xl', 'ha'  # Patterns typiques d'Unsplash
            ]

            # Vérifier si le nom contient des caractères suspects ou des patterns Unsplash
            has_suspicious_pattern = any(pattern in product_name.lower() for pattern in suspicious_patterns)
            has_random_chars = any(char.isdigit() and char.isupper() for char in product_name[-10:])  # Caractères aléatoires à la fin

            # Si le nom semble être un nom de fichier ou contient des patterns suspects
            if has_suspicious_pattern or len(product_name) > 30 or has_random_chars:
                # Essayer d'extraire un nom plus propre du début
                clean_name_parts = []
                words = product_name.split()

                for word in words:
                    # Arrêter si on trouve un mot suspect
                    if any(pattern in word.lower() for pattern in suspicious_patterns):
                        break
                    # Arrêter si le mot contient beaucoup de caractères mélangés
                    if len(word) > 8 and sum(c.isupper() for c in word) > 2:
                        break
                    clean_name_parts.append(word)

                if clean_name_parts and len(' '.join(clean_name_parts)) > 3:
                    product_name = ' '.join(clean_name_parts)
                else:
                    product_name = f"Produit #{product.id}"

            messages.success(request, f"{product_name} a été retiré de votre liste de souhaits")
        else:
            messages.warning(request, "Ce produit n'était pas dans votre liste de souhaits")

        return redirect('store:wishlist')

    except Exception as e:
        logger.error(f"Erreur remove_from_wishlist: {e}")
        messages.error(request, "Erreur lors de la suppression de la liste de souhaits")
        return redirect('store:wishlist')


def wishlist_view(request):
    """Afficher la liste de souhaits de l'utilisateur"""
    if not request.user.is_authenticated:
        messages.error(
            request, "Vous devez être connecté pour voir votre liste de souhaits"
        )
        return redirect("login")

    try:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
            "product"
        )

        context = {
            "wishlist_items": wishlist_items,
            "wishlist_count": wishlist_items.count(),
        }

        return render(request, "store/wishlist.html", context)

    except Exception as e:
        logger.error(f"Erreur wishlist_view: {e}")
        messages.error(request, "Erreur lors du chargement de votre liste de souhaits")
        return redirect("index")


def check_wishlist_status(request):
    """Vérifier si un produit est dans la wishlist (pour AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({"in_wishlist": False})

    try:
        product_id = request.GET.get("product_id")
        if not product_id:
            return JsonResponse({"in_wishlist": False})

        in_wishlist = Wishlist.objects.filter(
            user=request.user, product_id=product_id
        ).exists()

        return JsonResponse({"in_wishlist": in_wishlist})

    except Exception as e:
        logger.error(f"Erreur check_wishlist_status: {e}")
        return JsonResponse({"in_wishlist": False})
