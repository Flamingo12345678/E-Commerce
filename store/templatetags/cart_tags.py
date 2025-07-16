from django import template
from store.views import get_cart_summary

register = template.Library()


@register.simple_tag
def get_cart_info(user):
    """
    Retourne les informations du panier pour l'utilisateur connecté.

    Args:
        user: L'utilisateur Django

    Returns:
        dict: Dictionnaire avec total_items, total_price, is_empty
    """
    if not user.is_authenticated:
        return {
            "total_items": 0,
            "total_price": 0,
            "is_empty": True,
            "formatted_total": "0.00 €",
        }

    cart_data = get_cart_summary(user)

    # Ajouter le prix formaté
    cart_data["formatted_total"] = f"{cart_data['total_price']:.2f} €"

    return cart_data


@register.inclusion_tag("store/cart_badge.html")
def cart_badge(user):
    """
    Tag d'inclusion pour afficher le badge du panier.
    Utilise un template séparé pour une meilleure réutilisabilité.
    """
    cart_info = get_cart_info(user)
    return {"cart_info": cart_info}


@register.filter
def multiply(value, arg):
    """
    Filtre pour multiplier deux valeurs dans les templates.
    Utile pour les calculs de prix dans les templates.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
