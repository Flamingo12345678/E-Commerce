from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def format_price(value):
    """Formate un prix en euros"""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"
