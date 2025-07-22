"""
Vues pour l'authentification Firebase avec Google et Facebook
"""

import json
import logging
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from .firebase_auth import FirebaseAuthenticationBackend, FirebaseAuthHelper

logger = logging.getLogger(__name__)


class FirebaseAuthView(View):
    """Vue de base pour l'authentification Firebase"""

    def get(self, request):
        """Affiche la page de connexion Firebase"""
        if request.user.is_authenticated:
            return redirect("store:index")

        context = {
            "firebase_config": {
                "apiKey": getattr(settings, "FIREBASE_API_KEY", ""),
                "authDomain": getattr(settings, "FIREBASE_AUTH_DOMAIN", ""),
                "projectId": getattr(settings, "FIREBASE_PROJECT_ID", ""),
                "storageBucket": getattr(settings, "FIREBASE_STORAGE_BUCKET", ""),
                "messagingSenderId": getattr(
                    settings, "FIREBASE_MESSAGING_SENDER_ID", ""
                ),
                "appId": getattr(settings, "FIREBASE_APP_ID", ""),
            }
        }
        return render(request, "accounts/firebase_auth.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def firebase_login(request):
    """
    Connecte ou inscrit un utilisateur avec un token Firebase
    """
    try:
        data = json.loads(request.body)
        firebase_token = data.get("idToken")
        action = data.get("action", "login")  # "login" ou "signup"

        if not firebase_token:
            return JsonResponse(
                {"success": False, "error": "Token Firebase manquant"}, status=400
            )

        # Authentifier avec Firebase
        backend = FirebaseAuthenticationBackend()
        user = backend.authenticate(request, firebase_token=firebase_token)

        if user:
            # Connecter l'utilisateur dans Django
            login(
                request,
                user,
                backend="accounts.firebase_auth.FirebaseAuthenticationBackend",
            )

            message = "Inscription réussie" if action == "signup" else "Connexion réussie"
            logger.info(f"{message} Firebase pour {user.email}")

            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "redirect_url": reverse("index"),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "full_name": user.full_name,
                    },
                }
            )
        else:
            error_msg = "Échec de l'inscription" if action == "signup" else "Échec de l'authentification"
            return JsonResponse(
                {"success": False, "error": error_msg}, status=401
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Données JSON invalides"}, status=400
        )
    except Exception as e:
        logger.error(f"Erreur lors de la connexion Firebase: {e}")
        return JsonResponse(
            {"success": False, "error": "Erreur interne du serveur"}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def firebase_logout(request):
    """
    Déconnecte l'utilisateur
    """
    try:
        # Révoquer les tokens Firebase si disponible
        if request.user.is_authenticated and hasattr(request.user, "firebase_uid"):
            FirebaseAuthHelper.revoke_refresh_tokens(request.user.firebase_uid)

        logout(request)

        return JsonResponse({"success": True, "message": "Déconnexion réussie"})

    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion Firebase: {e}")
        return JsonResponse(
            {"success": False, "error": "Erreur lors de la déconnexion"}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def verify_firebase_token(request):
    """
    Vérifie un token Firebase sans connecter l'utilisateur
    """
    try:
        data = json.loads(request.body)
        firebase_token = data.get("idToken")

        if not firebase_token:
            return JsonResponse(
                {"success": False, "error": "Token Firebase manquant"}, status=400
            )

        # Vérifier le token
        decoded_token = FirebaseAuthHelper.verify_firebase_token(firebase_token)

        if decoded_token:
            return JsonResponse(
                {
                    "success": True,
                    "token_info": {
                        "uid": decoded_token.get("uid"),
                        "email": decoded_token.get("email"),
                        "email_verified": decoded_token.get("email_verified"),
                        "name": decoded_token.get("name"),
                        "picture": decoded_token.get("picture"),
                    },
                }
            )
        else:
            return JsonResponse(
                {"success": False, "error": "Token invalide"}, status=401
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Données JSON invalides"}, status=400
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {e}")
        return JsonResponse(
            {"success": False, "error": "Erreur interne du serveur"}, status=500
        )


@login_required
def firebase_profile(request):
    """
    Affiche le profil utilisateur avec les informations Firebase
    """
    context = {
        "user": request.user,
        "has_firebase_uid": hasattr(request.user, "firebase_uid")
        and request.user.firebase_uid,
    }
    return render(request, "accounts/firebase_profile.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def link_firebase_account(request):
    """
    Lie un compte Firebase existant à un compte Django
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error": "Utilisateur non authentifié"}, status=401
        )

    try:
        data = json.loads(request.body)
        firebase_token = data.get("idToken")

        if not firebase_token:
            return JsonResponse(
                {"success": False, "error": "Token Firebase manquant"}, status=400
            )

        # Vérifier le token Firebase
        decoded_token = FirebaseAuthHelper.verify_firebase_token(firebase_token)

        if not decoded_token:
            return JsonResponse(
                {"success": False, "error": "Token Firebase invalide"}, status=401
            )

        # Lier le compte Firebase à l'utilisateur Django
        user = request.user
        firebase_uid = decoded_token.get("uid")

        if hasattr(user, "firebase_uid"):
            user.firebase_uid = firebase_uid
            user.save()

            logger.info(f"Compte Firebase lié pour {user.email}")

            return JsonResponse(
                {"success": True, "message": "Compte Firebase lié avec succès"}
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Le modèle utilisateur ne supporte pas Firebase UID",
                },
                status=400,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Données JSON invalides"}, status=400
        )
    except Exception as e:
        logger.error(f"Erreur lors de la liaison du compte Firebase: {e}")
        return JsonResponse(
            {"success": False, "error": "Erreur interne du serveur"}, status=500
        )


def firebase_auth_status(request):
    """
    Retourne le statut d'authentification Firebase de l'utilisateur
    """
    if request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": True,
                "user": {
                    "id": request.user.id,
                    "email": request.user.email,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "full_name": request.user.full_name,
                },
                "has_firebase_uid": hasattr(request.user, "firebase_uid")
                and bool(request.user.firebase_uid),
            }
        )
    else:
        return JsonResponse(
            {
                "authenticated": False,
                "user": None,
                "has_firebase_uid": False,
            }
        )


class SocialAuthCallbackView(View):
    """
    Vue de callback pour les authentifications sociales (Google, Facebook)
    Cette vue sera appelée après la redirection depuis les providers sociaux
    """

    def get(self, request):
        """Gère les callbacks des providers sociaux"""
        provider = request.GET.get("provider", "")
        success = request.GET.get("success", "false").lower() == "true"

        if success:
            messages.success(request, f"Connexion {provider} réussie!")
            return redirect("store:index")
        else:
            error_message = request.GET.get("error", "Erreur d'authentification")
            messages.error(request, f"Erreur de connexion {provider}: {error_message}")
            return redirect("accounts:login")


def firebase_config_view(request):
    """
    Retourne la configuration Firebase pour le frontend
    """
    config = {
        "apiKey": getattr(settings, "FIREBASE_API_KEY", ""),
        "authDomain": getattr(settings, "FIREBASE_AUTH_DOMAIN", ""),
        "projectId": getattr(settings, "FIREBASE_PROJECT_ID", ""),
        "storageBucket": getattr(settings, "FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": getattr(settings, "FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": getattr(settings, "FIREBASE_APP_ID", ""),
    }

    return JsonResponse({"firebase_config": config})
