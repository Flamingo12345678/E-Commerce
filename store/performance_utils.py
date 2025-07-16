"""
Utilitaires de performance pour les vues de la boutique.
Fonctions de mise en cache et optimisations de requêtes.
"""

from django.core.cache import cache
from django.conf import settings
from store.models import Product, Cart, Order
from django.db.models import Prefetch


def get_featured_products(limit=10):
    """
    Récupère les produits vedettes avec mise en cache.

    Args:
        limit: Nombre de produits à retourner

    Returns:
        QuerySet: Produits optimisés pour l'affichage
    """
    cache_key = f"featured_products_{limit}"
    products = cache.get(cache_key)

    if products is None:
        products = (
            Product.objects.only("id", "name", "slug", "price", "thumbnail", "stock")
            .filter(stock__gt=0)  # Seulement les produits en stock
            .order_by("-created_at")[:limit]
        )

        # Mise en cache pour 15 minutes
        cache.set(cache_key, products, 60 * 15)

    return products


def get_cart_summary_cached(user):
    """
    Version mise en cache de get_cart_summary pour les utilisateurs authentifiés.

    Args:
        user: Utilisateur Django

    Returns:
        dict: Résumé du panier
    """
    if not user.is_authenticated:
        return {"orders": [], "total_items": 0, "total_price": 0, "is_empty": True}

    cache_key = f"cart_summary_{user.id}"
    cart_data = cache.get(cache_key)

    if cart_data is None:
        # Importer ici pour éviter les imports circulaires
        from store.views import get_cart_summary

        cart_data = get_cart_summary(user)

        # Mise en cache courte (2 minutes) car le panier change fréquemment
        cache.set(cache_key, cart_data, 60 * 2)

    return cart_data


def invalidate_cart_cache(user):
    """
    Invalide le cache du panier pour un utilisateur.
    À appeler lors des modifications du panier.

    Args:
        user: Utilisateur Django
    """
    if user.is_authenticated:
        cache_key = f"cart_summary_{user.id}"
        cache.delete(cache_key)


def get_optimized_cart_for_user(user):
    """
    Récupère le panier avec toutes les optimisations de requêtes.

    Args:
        user: Utilisateur Django

    Returns:
        Cart ou None: Panier optimisé avec relations pré-chargées
    """
    try:
        # Optimisation maximale avec prefetch personnalisé
        orders_prefetch = Prefetch(
            "orders",
            queryset=Order.objects.select_related("product").filter(ordered=False),
            to_attr="active_orders",
        )

        cart = (
            Cart.objects.select_related("user")
            .prefetch_related(orders_prefetch)
            .get(user=user)
        )

        return cart

    except Cart.DoesNotExist:
        return None


def get_product_stats_cached(product_id):
    """
    Récupère les statistiques d'un produit avec mise en cache.

    Args:
        product_id: ID du produit

    Returns:
        dict: Statistiques du produit
    """
    cache_key = f"product_stats_{product_id}"
    stats = cache.get(cache_key)

    if stats is None:
        from django.db.models import Count, Sum

        # Calculer les statistiques
        product = Product.objects.get(id=product_id)
        total_orders = Order.objects.filter(product=product, ordered=True).aggregate(
            count=Count("id"), total_quantity=Sum("quantity")
        )

        stats = {
            "total_sales": total_orders["count"] or 0,
            "total_quantity_sold": total_orders["total_quantity"] or 0,
            "stock_status": "en_stock" if product.stock > 0 else "epuise",
            "last_updated": product.updated_at,
        }

        # Cache plus long pour les stats (30 minutes)
        cache.set(cache_key, stats, 60 * 30)

    return stats


# Décorateur pour mesurer les performances des vues
def measure_performance(view_func):
    """
    Décorateur pour mesurer et logger les performances des vues.
    """

    def wrapper(*args, **kwargs):
        import time
        import logging
        from django.db import connection

        logger = logging.getLogger("performance")

        # Reset query counter
        initial_queries = len(connection.queries)
        start_time = time.time()

        # Exécuter la vue
        result = view_func(*args, **kwargs)

        # Mesurer
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        query_count = len(connection.queries) - initial_queries

        # Logger les performances
        logger.info(
            f"View {view_func.__name__}: "
            f"{execution_time:.2f}ms, {query_count} queries"
        )

        return result

    return wrapper
