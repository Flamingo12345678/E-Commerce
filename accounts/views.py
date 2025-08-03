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
        return redirect("index")

    try:
        if request.method == "POST":
            # 🔐 Évite les redirections POST anormales (ex: depuis Firebase)
            if not request.POST.get("form_type") == "classic_signup":
                return redirect("signup")

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
                    messages.success(
                        request,messages.success "Votre compte a été créé avec succès.")
            except IntegrityError:
                messages.error(
                    request, "Une erreur s'est produite lors de la création du compte."
                )
            except Exception as e:
                messages.error(request, "Une erreur inattendue s'est produite.")

        return render(request, "accounts/signup.html", {
            'firebase_config': get_firebase_config()
        })

    except SessionInterrupted:
        messages.error(request, "Session interrompue. Veuillez réessayer.")
        return redirect("signup")


def login_user(request):
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        messages.error(request, "Session interrompue. Veuillez réessayer.")

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
                    from django_otp.plugins.otp_totp.models import TOTPDevice

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
                            or "index"
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
                        request.GET.get("next") or request.POST.get("next") or "index"
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

    return redirect("index")


def profile(request):
    """Affiche et permet de modifier le profil utilisateur"""
    if not request.user.is_authenticated:
        messages.warning(
            request, "Vous devez être connecté pour accéder à votre profil."
        )
        return redirect("login")

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
            user.phone_number = phone_number
            user.address = address

            # Gestion de la date de naissance
            if date_of_birth:
                from datetime import datetime

                try:
                    # Convertir la chaîne de date en objet date
                    user.birth_date = datetime.strptime(
                        date_of_birth, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    messages.error(request, "Format de date invalide.")
                    return render(request, "accounts/profile.html")
            else:
                user.birth_date = None

            user.newsletter_subscription = newsletter
            user.save()

            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect("profile")

        except Exception as e:
            messages.error(request, "Une erreur s'est produite lors de la mise à jour.")

    return render(request, "accounts/profile.html")


def change_password(request):
    """Permet de changer le mot de passe"""
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

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
            return redirect("profile")

        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)

    return render(request, "accounts/change_password.html")


# Nouvelles vues pour les actions du profil


@login_required
def export_user_data(request):
    """Exporte toutes les données utilisateur au format JSON"""
    user = request.user

    # Récupérer les commandes de l'utilisateur
    from store.models import Order

    orders = Order.objects.filter(user=user, ordered=True).select_related("product")

    user_data = {
        "user_info": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "profile_data": {
            "phone_number": getattr(user, "phone_number", ""),
            "address": getattr(user, "address", ""),
            "newsletter_subscription": getattr(user, "newsletter_subscription", False),
        },
        "orders": [
            {
                "id": order.id,
                "product_name": order.product.name,
                "quantity": order.quantity,
                "price": str(order.product.price),
                "total": str(order.total_price),
                "date_ordered": (
                    order.date_ordered.isoformat() if order.date_ordered else None
                ),
            }
            for order in orders
        ],
        "export_date": datetime.now().isoformat(),
    }

    response = HttpResponse(
        json.dumps(user_data, indent=2, ensure_ascii=False),
        content_type="application/json",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="user_data_{user.username}_{datetime.now().strftime("%Y%m%d")}.json"'
    )

    messages.success(request, "Vos données ont été exportées avec succès.")
    return response


@login_required
@require_POST
def delete_user_account(request):
    """Supprime définitivement le compte utilisateur"""
    password = request.POST.get("password", "")

    if not request.user.check_password(password):
        messages.error(request, "Mot de passe incorrect.")
        return redirect("profile")

    try:
        with transaction.atomic():
            username = request.user.username

            # Marquer les commandes comme "compte supprimé" plutôt que de les supprimer
            from store.models import Order

            Order.objects.filter(user=request.user).update(user=None)

            # Supprimer le compte
            request.user.delete()

            messages.success(
                request, f"Le compte {username} a été supprimé définitivement."
            )
            return redirect("index")

    except Exception as e:
        messages.error(request, "Erreur lors de la suppression du compte.")
        return redirect("profile")


@login_required
def manage_addresses(request):
    """Gère les adresses de l'utilisateur"""
    from .models import Address

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            address_type = request.POST.get("address_type", "home")
            street = request.POST.get("street", "").strip()
            city = request.POST.get("city", "").strip()
            state = request.POST.get("state", "").strip()
            postal_code = request.POST.get("postal_code", "").strip()
            country = request.POST.get("country", "France").strip()

            if not all([street, city, postal_code]):
                messages.error(
                    request, "Veuillez remplir tous les champs obligatoires."
                )
                return redirect("profile")

            # Créer une nouvelle adresse
            try:
                # Si c'est la première adresse, la marquer comme par défaut
                is_default = not Address.objects.filter(user=request.user).exists()

                Address.objects.create(
                    user=request.user,
                    address_type=address_type,
                    street=street,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    country=country,
                    is_default=is_default,
                )

                messages.success(request, "Adresse ajoutée avec succès.")

            except Exception as e:
                messages.error(request, "Erreur lors de l'ajout de l'adresse.")

        elif action == "delete":
            address_id = request.POST.get("address_id")
            try:
                address = Address.objects.get(id=address_id, user=request.user)
                address.delete()
                messages.success(request, "Adresse supprimée avec succès.")
            except Address.DoesNotExist:
                messages.error(request, "Adresse introuvable.")
            except Exception as e:
                messages.error(request, "Erreur lors de la suppression.")

        elif action == "set_default":
            address_id = request.POST.get("address_id")
            try:
                # Retirer le statut par défaut de toutes les adresses
                Address.objects.filter(user=request.user).update(is_default=False)
                # Marquer l'adresse sélectionnée comme par défaut
                address = Address.objects.get(id=address_id, user=request.user)
                address.is_default = True
                address.save()
                messages.success(request, "Adresse par défaut mise à jour.")
            except Address.DoesNotExist:
                messages.error(request, "Adresse introuvable.")
            except Exception as e:
                messages.error(request, "Erreur lors de la mise à jour.")

    return redirect("profile")


@login_required
def manage_payment_methods(request):
    """Gère les méthodes de paiement (simulation)"""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            card_number = request.POST.get("card_number", "").strip()
            card_name = request.POST.get("card_name", "").strip()
            expiry_date = request.POST.get("expiry_date", "").strip()
            cvv = request.POST.get("cvv", "").strip()

            if not all([card_number, card_name, expiry_date, cvv]):
                messages.error(request, "Veuillez remplir tous les champs.")
                return redirect("profile")

            # Formatage automatique de la date d'expiration
            formatted_expiry = format_expiry_date(expiry_date)

            # Validations avec les utilitaires Python
            if not validate_card_number(card_number):
                messages.error(request, "Numéro de carte invalide.")
                return redirect("profile")

            if not validate_expiry_date(formatted_expiry):
                messages.error(request, "Date d'expiration invalide.")
                return redirect("profile")

            if not validate_cvv(cvv):
                messages.error(request, "CVV invalide.")
                return redirect("profile")

            # Simulation - en réalité, on ne stockerait jamais les données
            masked_card = mask_card_number(card_number)
            messages.success(
                request,
                f"Carte de paiement {masked_card} ajoutée avec succès.",
            )

        elif action == "delete":
            messages.success(request, "Méthode de paiement supprimée.")

    return redirect("profile")


@login_required
@require_POST
def update_notifications(request):
    """Met à jour les préférences de notification"""
    email_notifications = request.POST.get("email_notifications") == "on"
    sms_notifications = request.POST.get("sms_notifications") == "on"
    push_notifications = request.POST.get("push_notifications") == "on"

    # Sauvegarder les préférences (pour l'instant dans les attributs utilisateur)
    user = request.user
    user.email_notifications = email_notifications
    user.sms_notifications = sms_notifications
    user.push_notifications = push_notifications
    user.save()

    messages.success(request, "Préférences de notification mises à jour.")
    return redirect("profile")


@login_required
def setup_two_factor(request):
    """Configuration de l'authentification à deux facteurs avec django-otp"""
    user = request.user

    if request.method == "POST":
        action = request.POST.get("action")
        current_password = request.POST.get("current_password", "").strip()
        verification_code = request.POST.get("verification_code", "").strip()

        # Vérifier le mot de passe actuel
        if not user.check_password(current_password):
            messages.error(request, "Mot de passe incorrect.")
            return redirect("profile")

        if action == "enable":
            # Vérifier si l'utilisateur n'a pas déjà un dispositif TOTP
            if not user_has_device(user):
                # Si un code de vérification est fourni, vérifier le dispositif temporaire
                if verification_code:
                    # Récupérer le dispositif temporaire depuis la session
                    temp_device_key = request.session.get("temp_2fa_key")
                    if not temp_device_key:
                        messages.error(
                            request, "Session expirée. Recommencez la configuration."
                        )
                        return redirect("profile")

                    # Vérifier le code TOTP avec une méthode manuelle
                    from django_otp.oath import totp
                    from binascii import unhexlify
                    import time

                    # Convertir la clé hexadécimale en binaire
                    try:
                        key_bytes = unhexlify(temp_device_key.encode())
                        # Calculer le code TOTP attendu
                        current_time = int(time.time()) // 30
                        expected_code = totp(key_bytes, step=30)
                        expected_code_str = f"{expected_code:06d}"

                        is_valid_code = verification_code == expected_code_str
                    except Exception:
                        is_valid_code = False

                    if is_valid_code:
                        # Code valide, finaliser l'activation
                        device = TOTPDevice.objects.create(
                            user=user,
                            name="default",
                            confirmed=True,
                            key=temp_device_key,
                        )

                        # Activer 2FA pour l'utilisateur
                        user.two_factor_enabled = True
                        user.save()

                        # Nettoyer la session
                        del request.session["temp_2fa_key"]

                        messages.success(
                            request,
                            "Authentification à deux facteurs activée avec succès!",
                        )
                        return redirect("profile")
                    else:
                        messages.error(
                            request,
                            "Code de vérification invalide. Vérifiez votre application d'authentification.",
                        )
                        return HttpResponseRedirect(
                            reverse("profile") + "?show_qr=1&verify=1"
                        )

                else:
                    # Première étape : créer un dispositif temporaire
                    from binascii import hexlify
                    import os

                    temp_key = hexlify(os.urandom(20)).decode("ascii")
                    request.session["temp_2fa_key"] = temp_key

                    messages.success(
                        request,
                        "Scannez le QR code avec votre application d'authentification, "
                        "puis entrez le code généré pour confirmer.",
                    )
                    return HttpResponseRedirect(
                        reverse("profile") + "?show_qr=1&verify=1"
                    )
            else:
                messages.info(request, "Authentification déjà activée.")

        elif action == "disable":
            # Supprimer tous les dispositifs TOTP de l'utilisateur
            TOTPDevice.objects.filter(user=user).delete()

            # Mettre à jour le champ dans notre modèle utilisateur
            user.two_factor_enabled = False
            user.save()

            messages.success(request, "Authentification à deux facteurs désactivée.")

    return redirect("profile")


@login_required
def two_factor_qr(request):
    """Génère le QR code pour l'authentification à deux facteurs"""
    user = request.user

    # Vérifier s'il s'agit d'une vérification (dispositif temporaire)
    is_verification = request.GET.get("verify") == "1"

    if is_verification:
        # Utiliser la clé temporaire de la session
        temp_key = request.session.get("temp_2fa_key")
        if not temp_key:
            return HttpResponse("Session expirée", status=404)

        # Créer un dispositif temporaire pour générer l'URL
        temp_device = TOTPDevice(user=user, name="temp", key=temp_key)
        provisioning_uri = temp_device.config_url
    else:
        # Obtenir le dispositif TOTP permanent de l'utilisateur
        device = TOTPDevice.objects.filter(user=user, name="default").first()
        if not device:
            return HttpResponse("Dispositif non trouvé", status=404)

        # Utiliser la méthode config_url de django-otp
        provisioning_uri = device.config_url

    # Générer le QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    # Créer l'image SVG
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)

    # Convertir en chaîne
    stream = BytesIO()
    img.save(stream)
    svg_string = stream.getvalue().decode()

    return HttpResponse(svg_string, content_type="image/svg+xml")


@login_required
def connect_social_account(request):
    """Connecte/déconnecte des comptes sociaux (simulation)"""
    if request.method == "POST":
        provider = request.POST.get("provider")
        action = request.POST.get("action")

        if action == "connect":
            # Simulation de connexion de compte social
            messages.success(
                request, f"Compte {provider.title()} connecté avec succès."
            )

        elif action == "disconnect":
            # Simulation de déconnexion de compte social
            messages.success(request, f"Compte {provider.title()} déconnecté.")

    return redirect("profile")


@login_required
def profile_edit_modal(request):
    """Vue pour l'édition rapide du profil via modal"""
    if request.method == "POST":
        field = request.POST.get("field")
        value = request.POST.get("value", "").strip()

        if field == "first_name":
            request.user.first_name = value
        elif field == "last_name":
            request.user.last_name = value
        elif field == "email":
            if value and not re.match(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value
            ):
                return JsonResponse({"success": False, "error": "Email invalide"})
            request.user.email = value
        elif field == "phone_number":
            request.user.phone_number = value

        try:
            request.user.save()
            return JsonResponse({"success": True, "message": "Profil mis à jour"})
        except Exception:
            return JsonResponse(
                {"success": False, "error": "Erreur lors de la sauvegarde"}
            )

    return JsonResponse({"success": False, "error": "Méthode non autorisée"})


def password_reset_request(request):
    """Vue pour demander une réinitialisation de mot de passe"""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Veuillez saisir votre adresse email.")
            return render(request, "accounts/password_reset.html")

        try:
            user = User.objects.get(email=email)

            # Générer le token et l'UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Créer le lien de réinitialisation
            reset_url = request.build_absolute_uri(
                reverse(
                    "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
                )
            )

            # Préparer le contexte pour l'email
            context = {
                "user": user,
                "reset_url": reset_url,
                "site_name": "YEE",
            }

            # Envoyer l'email (pour l'instant, on affiche juste un message)
            # TODO: Configurer l'envoi d'email en production
            # send_mail(
            #     'Réinitialisation de votre mot de passe',
            #     render_to_string('accounts/password_reset_email.txt', context),
            #     settings.DEFAULT_FROM_EMAIL,
            #     [email],
            #     html_message=render_to_string('accounts/password_reset_email.html', context),
            # )

            messages.success(
                request,
                "Si cette adresse email existe dans notre système, vous recevrez un lien de réinitialisation.",
            )
            return render(request, "accounts/password_reset_done.html")

        except User.DoesNotExist:
            # Ne pas révéler si l'email existe ou non pour des raisons de sécurité
            messages.success(
                request,
                "Si cette adresse email existe dans notre système, vous recevrez un lien de réinitialisation.",
            )
            return render(request, "accounts/password_reset_done.html")

    return render(request, "accounts/password_reset.html")


def password_reset_confirm(request, uidb64, token):
    """Vue pour confirmer la réinitialisation de mot de passe"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if new_password != confirm_password:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return render(
                    request,
                    "accounts/password_reset_confirm.html",
                    {"valid_link": True, "uidb64": uidb64, "token": token},
                )

            try:
                validate_password(new_password, user)
                user.set_password(new_password)
                user.save()

                messages.success(
                    request, "Votre mot de passe a été réinitialisé avec succès."
                )
                return redirect("login")

            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(
                    request,
                    "accounts/password_reset_confirm.html",
                    {"valid_link": True, "uidb64": uidb64, "token": token},
                )

        return render(
            request,
            "accounts/password_reset_confirm.html",
            {"valid_link": True, "uidb64": uidb64, "token": token},
        )
    else:
        messages.error(request, "Le lien de réinitialisation est invalide ou a expiré.")
        return redirect("login")

    return JsonResponse({"success": False, "error": "Méthode non autorisée"})
