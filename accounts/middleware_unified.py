# -*- coding: utf-8 -*-
"""
    accounts.middleware_unified
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Middleware pour gérer l'authentification unifiée Django/Firebase
"""
import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.http import JsonResponse
from django.conf import settings
from .firebase_auth import verify_firebase_token

logger = logging.getLogger(__name__)


class UnifiedAuthMiddleware:
    """Middleware pour gérer l'authentification unifiée"""

    def __init__(self, get_response):
        self.get_response = get_response
        # URLs qui ne nécessitent pas d'authentification
        self.public_urls = [
            '/accounts/auth/',
            '/accounts/auth/signup/',
            '/accounts/login/',
            '/accounts/signup/',
            '/accounts/firebase/',
            '/accounts/password-reset/',
            '/media/',
            '/static/',
            '/admin/',
            '/',
        ]

        # URLs pour l'authentification unifiée
        self.unified_auth_urls = [
            '/accounts/auth/',
            '/accounts/auth/signup/',
            '/accounts/auth/logout/',
            '/accounts/auth/profile/',
            '/accounts/auth/status/',
            '/accounts/auth/link-accounts/',
        ]

    def __call__(self, request):
        # Traitement avant la vue
        self.process_request(request)

        response = self.get_response(request)

        # Traitement après la vue
        return self.process_response(request, response)

    def process_request(self, request):
        """Traite la requête avant qu'elle n'atteigne la vue"""
        # Vérifier si c'est une URL publique
        if any(request.path.startswith(url) for url in self.public_urls):
            return None

        # Vérifier l'état d'authentification Firebase dans les headers
        firebase_token = request.META.get('HTTP_AUTHORIZATION')
        if firebase_token and firebase_token.startswith('Bearer '):
            token = firebase_token.split(' ')[1]
            try:
                decoded_token = verify_firebase_token(token)
                if decoded_token:
                    # Token valide, ajouter les informations à la requête
                    request.firebase_user = decoded_token
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du token Firebase: {e}")

    def process_response(self, request, response):
        """Traite la réponse avant qu'elle ne soit envoyée au client"""
        # Ajouter des headers pour l'authentification unifiée
        if hasattr(request, 'user') and request.user.is_authenticated:
            response['X-Auth-Status'] = 'authenticated'
            response['X-Auth-Type'] = 'firebase' if not request.user.has_usable_password() else 'django'
        else:
            response['X-Auth-Status'] = 'anonymous'

        return response

    def should_redirect_to_unified(self, request):
        """Détermine si on doit rediriger vers le système unifié"""
        # Rediriger vers le système unifié si activé dans les settings
        return getattr(settings, 'USE_UNIFIED_AUTH', False)


class AuthRedirectMiddleware:
    """Middleware pour rediriger automatiquement vers le système unifié"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.redirect_mappings = {
            '/accounts/login/': '/accounts/auth/',
            '/accounts/signup/': '/accounts/auth/signup/',
            '/accounts/logout/': '/accounts/auth/logout/',
            '/accounts/profile/': '/accounts/auth/profile/',
        }

    def __call__(self, request):
        # Vérifier si on doit rediriger vers le système unifié
        if getattr(settings, 'USE_UNIFIED_AUTH', False):
            if request.path in self.redirect_mappings:
                # Préserver les paramètres GET (comme 'next')
                redirect_url = self.redirect_mappings[request.path]
                if request.GET:
                    query_string = request.GET.urlencode()
                    redirect_url += f'?{query_string}'
                return redirect(redirect_url)

        response = self.get_response(request)
        return response


class FirebaseTokenMiddleware:
    """Middleware pour gérer les tokens Firebase dans les cookies"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si un token Firebase est présent dans les cookies
        firebase_token = request.COOKIES.get('firebase_token')

        if firebase_token and not request.user.is_authenticated:
            try:
                # Vérifier le token Firebase
                decoded_token = verify_firebase_token(firebase_token)
                if decoded_token:
                    # Token valide, mais l'utilisateur n'est pas connecté
                    # Cela peut arriver après un redémarrage du serveur
                    request.firebase_token_available = True
                    request.firebase_user_info = decoded_token
            except Exception as e:
                logger.error(f"Token Firebase invalide dans les cookies: {e}")
                # Supprimer le token invalide
                request.firebase_token_invalid = True

        response = self.get_response(request)

        # Supprimer les tokens invalides des cookies
        if hasattr(request, 'firebase_token_invalid'):
            response.delete_cookie('firebase_token')

        return response


class UserActivityMiddleware:
    """Middleware pour tracker l'activité des utilisateurs"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Logger l'activité d'authentification
        if hasattr(request, 'user') and request.user.is_authenticated:
            auth_type = 'firebase' if not request.user.has_usable_password() else 'django'

            # Mettre à jour la dernière activité (peut être ajouté au modèle User)
            if hasattr(request.user, 'last_activity'):
                from django.utils import timezone
                request.user.last_activity = timezone.now()
                request.user.save(update_fields=['last_activity'])

            # Logger pour les statistiques
            logger.info(f"Activité utilisateur - {request.user.email} - Type: {auth_type} - URL: {request.path}")

        return response
