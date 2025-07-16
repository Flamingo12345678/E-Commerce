"""
Utilitaires pour le module accounts
"""

import re
from datetime import datetime


def format_card_number(card_number):
    """
    Formate un numéro de carte en ajoutant des espaces tous les 4 chiffres

    Args:
        card_number (str): Numéro de carte brut

    Returns:
        str: Numéro de carte formaté (ex: "1234 5678 9012 3456")
    """
    if not card_number:
        return ""

    # Supprimer tous les caractères non numériques
    digits = re.sub(r"\D", "", card_number)

    # Ajouter un espace tous les 4 chiffres
    formatted = ""
    for i, digit in enumerate(digits):
        if i > 0 and i % 4 == 0:
            formatted += " "
        formatted += digit

    return formatted


def format_expiry_date(expiry_date):
    """
    Formate une date d'expiration au format MM/YY

    Args:
        expiry_date (str): Date d'expiration brute

    Returns:
        str: Date formatée (ex: "12/25")
    """
    if not expiry_date:
        return ""

    # Supprimer tous les caractères non numériques
    digits = re.sub(r"\D", "", expiry_date)

    if len(digits) >= 2:
        month = digits[:2]
        year = digits[2:4] if len(digits) >= 4 else ""
        if year:
            return f"{month}/{year}"
        else:
            return month

    return digits


def clean_card_number(card_number):
    """
    Nettoie un numéro de carte en supprimant les espaces et caractères spéciaux

    Args:
        card_number (str): Numéro de carte avec espaces/caractères

    Returns:
        str: Numéro de carte nettoyé (chiffres uniquement)
    """
    if not card_number:
        return ""

    return re.sub(r"\D", "", card_number)


def validate_card_number(card_number):
    """
    Valide un numéro de carte (13-19 chiffres)

    Args:
        card_number (str): Numéro de carte à valider

    Returns:
        bool: True si valide, False sinon
    """
    clean_number = clean_card_number(card_number)
    return len(clean_number) >= 13 and len(clean_number) <= 19


def validate_expiry_date(expiry_date):
    """
    Valide une date d'expiration (MM/YY)

    Args:
        expiry_date (str): Date d'expiration à valider

    Returns:
        bool: True si valide, False sinon
    """
    if not expiry_date:
        return False

    try:
        # Format attendu: MM/YY
        if "/" not in expiry_date:
            return False

        month, year = expiry_date.split("/")

        # Vérifier le mois (01-12)
        if not month.isdigit() or int(month) < 1 or int(month) > 12:
            return False

        # Vérifier l'année (format YY)
        if not year.isdigit() or len(year) != 2:
            return False

        # Vérifier que la date n'est pas dans le passé
        current_year = datetime.now().year % 100  # Derniers 2 chiffres
        current_month = datetime.now().month

        card_year = int(year)
        card_month = int(month)

        if card_year < current_year:
            return False
        elif card_year == current_year and card_month < current_month:
            return False

        return True

    except (ValueError, IndexError):
        return False


def validate_cvv(cvv):
    """
    Valide un CVV (3-4 chiffres)

    Args:
        cvv (str): CVV à valider

    Returns:
        bool: True si valide, False sinon
    """
    if not cvv:
        return False

    return cvv.isdigit() and len(cvv) in [3, 4]


def mask_card_number(card_number):
    """
    Masque un numéro de carte en ne gardant que les 4 derniers chiffres

    Args:
        card_number (str): Numéro de carte complet

    Returns:
        str: Numéro masqué (ex: "**** **** **** 3456")
    """
    clean_number = clean_card_number(card_number)

    if len(clean_number) < 4:
        return "*" * len(clean_number)

    # Garder les 4 derniers chiffres
    last_four = clean_number[-4:]

    # Créer le masque avec des groupes de 4
    masked_groups = []
    remaining_length = len(clean_number) - 4

    while remaining_length > 0:
        if remaining_length >= 4:
            masked_groups.append("****")
            remaining_length -= 4
        else:
            masked_groups.append("*" * remaining_length)
            remaining_length = 0

    masked_groups.append(last_four)

    return " ".join(masked_groups)
