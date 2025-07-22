"""
Context processors pour rendre les données globales disponibles dans tous les templates.
"""

from django.core.cache import cache
from store.models import Category


def global_categories(request):
    """
    Context processor pour rendre les catégories disponibles globalement.
    """
    # Utiliser le cache pour éviter des requêtes répétées
    categories = cache.get("global_categories")
    if categories is None:
        categories = Category.objects.filter(is_active=True).order_by(
            "display_order", "name"
        )
        cache.set("global_categories", categories, 3600)  # Cache 1h

    featured_categories = cache.get("global_featured_categories")
    if featured_categories is None:
        featured_categories = Category.objects.filter(
            is_featured=True, is_active=True
        ).order_by("display_order", "name")[:6]
        cache.set("global_featured_categories", featured_categories, 3600)

    return {
        "global_categories": categories,
        "global_featured_categories": featured_categories,
    }


def cart_info(request):
    """
    Context processor pour le panier disponible globalement.
    """
    if not request.user.is_authenticated:
        return {
            "cart_total_items": 0,
            "cart_total_price": 0,
            "cart_is_empty": True,
        }

    # Utiliser la fonction existante
    from store.views import get_cart_summary

    cart_data = get_cart_summary(request.user)

    return {
        "cart_total_items": cart_data["total_items"],
        "cart_total_price": cart_data["total_price"],
        "cart_is_empty": cart_data["is_empty"],
    }
