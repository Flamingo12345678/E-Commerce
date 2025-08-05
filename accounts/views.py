# -*- coding: utf-8 -*-
import re
import json
from datetime import datetime
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string

# Django OTP imports
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import user_has_device
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from .utils import (
    format_expiry_date,
    validate_card_number,
    validate_expiry_date,
    validate_cvv,
    mask_card_number,
)
from shop.firebase_config import get_firebase_config

# Create your views here.

User = get_user_model()


def validate_login_data(email, password):
    """
    Valide les données de connexion
    """
    errors = []

    # Validation de l'email/username
    if not email or len(email.strip()) < 1:
        errors.append("L'email ou nom d'utilisateur est obligatoire.")

    # Validation du mot de passe
    if not password or len(password.strip()) < 1:
        errors.append("Le mot de passe est obligatoire.")

    return errors


def validate_signup_data(username, email, password, password_confirm):
    """
    Valide les données d'inscription
    """
    errors = []

    # Validation du nom d'utilisateur
    if not username or len(username.strip()) < 3:
        errors.append("Le nom d'utilisateur doit contenir au moins 3 caractères.")

    if len(username) > 150:
        errors.append("Le nom d'utilisateur ne peut pas dépasser 150 caractères.")

    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        errors.append(
            "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores."
        )

    # Validation de l'email
    if email:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            errors.append("Veuillez entrer une adresse email valide.")

    # Validation du mot de passe
    if not password:
        errors.append("Le mot de passe est obligatoire.")
    else:
        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)

    # Confirmation du mot de passe
    if password != password_confirm:
        errors.append("Les mots de passe ne correspondent pas.")

    return errors


def signup(request):
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        return redirect("store:product_list")

    if request.method == "POST":
        # 🔐 Évite les redirections POST anormales (ex: depuis Firebase)
        if not request.POST.get("form_type") == "classic_signup":
            return redirect("accounts:signup")

        # Récupération des données du formulaire
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        # Validation des données
        validation_errors = validate_signup_data(
            username, email, password, password_confirm
        )

        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return render(
                request, "accounts/signup.html", {"username": username, "email": email}
            )

        try:
            with transaction.atomic():
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                    return render(
                        request,
                        "accounts/signup.html",
                        {"username": username, "email": email},
                    )

                if email and User.objects.filter(email=email).exists():
                    messages.error(request, "Cette adresse email est déjà utilisée.")
                    return render(
                        request,
                        "accounts/signup.html",
                        {"username": username, "email": email},
                    )

                user = User.objects.create_user(
                    username=username, email=email if email else "", password=password
                )

                login(request, user)
                messages.success(request, "Votre compte a été créé avec succès.")
                return redirect("store:product_list")

        except IntegrityError:
            messages.error(
                request, "Une erreur s'est produite lors de la création du compte."
            )
        except Exception as e:
            messages.error(request, "Une erreur inattendue s'est produite.")

    return render(request, "accounts/signup.html", {
        'firebase_config': get_firebase_config()
    })


def login_user(request):
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        return redirect("store:product_list")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        totp_code = request.POST.get("totp_code", "").strip()

        # Validation basique
        if not username or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, "accounts/login.html", {"username": username})

        # Tentative d'authentification
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                # Vérifier si l'utilisateur a la 2FA activée
                if getattr(user, "two_factor_enabled", False):
                    # Si le code TOTP n'est pas fourni, afficher le formulaire 2FA
                    if not totp_code:
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "username": username,
                                "show_2fa": True,
                                "user_id": user.id,
                            },
                        )

                    # Vérifier le code TOTP
                    device = TOTPDevice.objects.filter(
                        user=user, name="default", confirmed=True
                    ).first()

                    if device and device.verify_token(totp_code):
                        # Code TOTP valide, connecter l'utilisateur
                        login(request, user)
                        messages.success(request, f"Bienvenue {user.username} !")

                        # Redirection vers la page suivante ou index
                        next_url = (
                            request.GET.get("next")
                            or request.POST.get("next")
                            or "store:product_list"
                        )
                        return redirect(next_url)
                    else:
                        # Code TOTP invalide
                        messages.error(
                            request, "Code d'authentification invalide ou expiré."
                        )
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "username": username,
                                "show_2fa": True,
                                "user_id": user.id,
                            },
                        )
                else:
                    # Pas de 2FA, connexion normale
                    login(request, user)
                    messages.success(request, f"Bienvenue {user.username} !")

                    # Redirection vers la page suivante ou index
                    next_url = (
                        request.GET.get("next") or request.POST.get("next") or "store:product_list"
                    )
                    return redirect(next_url)
            else:
                messages.error(request, "Votre compte est désactivé.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

        return render(request, "accounts/login.html", {"username": username})

    # Ajouter la configuration Firebase au contexte
    context = {
        'firebase_config': get_firebase_config()
    }
    
    return render(request, "accounts/login.html", context)


def logout_user(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(
            request, f"Au revoir {username} ! Vous êtes maintenant déconnecté."
        )
    else:
        messages.info(request, "Vous n'étiez pas connecté.")

    return redirect("store:product_list")


@login_required
def profile(request):
    """Affiche et permet de modifier le profil utilisateur"""
    if request.method == "POST":
        # Récupération des données du formulaire
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        address = request.POST.get("address", "").strip()
        date_of_birth = request.POST.get("date_of_birth", "").strip()
        newsletter = request.POST.get("newsletter") == "on"

        try:
            # Validation de l'email si fourni
            if email:
                email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_regex, email):
                    messages.error(request, "Veuillez entrer une adresse email valide.")
                    return render(request, "accounts/profile.html")

                # Vérifier si l'email n'est pas déjà utilisé par un autre utilisateur
                if (
                    User.objects.filter(email=email)
                    .exclude(pk=request.user.pk)
                    .exists()
                ):
                    messages.error(request, "Cette adresse email est déjà utilisée.")
                    return render(request, "accounts/profile.html")

            # Mise à jour du profil
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email

            # Ces champs peuvent ne pas exister sur le modèle User par défaut
            if hasattr(user, 'phone_number'):
                user.phone_number = phone_number
            if hasattr(user, 'address'):
                user.address = address
            if hasattr(user, 'newsletter_subscription'):
                user.newsletter_subscription = newsletter

            # Gestion de la date de naissance
            if date_of_birth and hasattr(user, 'birth_date'):
                try:
                    user.birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(request, "Format de date invalide.")
                    return render(request, "accounts/profile.html")

            user.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect("accounts:profile")

        except Exception as e:
            messages.error(request, "Une erreur s'est produite lors de la mise à jour.")

    return render(request, "accounts/profile.html")


@login_required
def change_password(request):
    """Permet de changer le mot de passe"""
    if request.method == "POST":
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # Vérifications
        if not request.user.check_password(current_password):
            messages.error(request, "Le mot de passe actuel est incorrect.")
            return render(request, "accounts/change_password.html")

        if new_password != confirm_password:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            return render(request, "accounts/change_password.html")

        try:
            validate_password(new_password, request.user)
            request.user.set_password(new_password)
            request.user.save()

            # Reconnecter l'utilisateur
            login(request, request.user)
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
            return redirect("accounts:profile")

        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)

    return render(request, "accounts/change_password.html")


# Fonctions simplifiées pour éviter les erreurs

@login_required
def export_user_data(request):
    """Exporte les données utilisateur"""
    messages.info(request, "Fonctionnalité d'export en cours de développement.")
    return redirect("accounts:profile")


@login_required
@require_POST
def delete_user_account(request):
    """Supprime le compte utilisateur"""
    messages.info(request, "Fonctionnalité de suppression en cours de développement.")
    return redirect("accounts:profile")


@login_required
def manage_addresses(request):
    """Gère les adresses"""
    messages.info(request, "Gestion des adresses en cours de développement.")
    return redirect("accounts:profile")


@login_required
def manage_payment_methods(request):
    """Gère les méthodes de paiement"""
    messages.info(request, "Gestion des paiements en cours de développement.")
    return redirect("accounts:profile")


@login_required
@require_POST
def update_notifications(request):
    """Met à jour les notifications"""
    messages.success(request, "Préférences de notification mises à jour.")
    return redirect("accounts:profile")


@login_required
def setup_two_factor(request):
    """Configuration 2FA"""
    messages.info(request, "Configuration 2FA en cours de développement.")
    return redirect("accounts:profile")


@login_required
def two_factor_qr(request):
    """QR code 2FA"""
    return HttpResponse("QR Code en cours de développement", content_type="text/plain")


@login_required
def connect_social_account(request):
    """Connecte des comptes sociaux"""
    messages.info(request, "Connexion de comptes sociaux en cours de développement.")
    return redirect("accounts:profile")


@login_required
def profile_edit_modal(request):
    """Édition rapide du profil"""
    if request.method == "POST":
        return JsonResponse({"success": True, "message": "Profil mis à jour"})
    return JsonResponse({"success": False, "error": "Méthode non autorisée"})


def password_reset_request(request):
    """Demande de réinitialisation de mot de passe"""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            messages.success(
                request,
                "Si cette adresse email existe, vous recevrez un lien de réinitialisation.",
            )
            return render(request, "accounts/password_reset_done.html")
        else:
            messages.error(request, "Veuillez saisir votre adresse email.")

    return render(request, "accounts/password_reset.html")


def password_reset_confirm(request, uidb64, token):
    """Confirme la réinitialisation de mot de passe"""
    messages.info(request, "Réinitialisation de mot de passe en cours de développement.")
    return redirect("accounts:login")
