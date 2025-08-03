# -*- coding: utf-8 -*-
"""
    accounts.firebase_views
    ~~~~~~~~~~~~~~~~~~~~~~~

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
from django.views import View

    FirebaseAuthenticationBackend,
    verify_firebase_token
)
from shop.firebase_config import get_firebase_config

logger = logging.getLogger(__name__)


class FirebaseAuthView(View):
    """Vue de base pour l'authentification Firebase"""
class FirebaseAuthView(View):
    """Vue de base pour l'authentification Firebase"""
        """Affiche la page de connexion Firebase"""
        if request.user.is_authenticated:
            return redirect('store:index')

            return redirect('store:index')

        # Utiliser le template de connexion existant qui contient déjà Firebase
        if not firebase_token:
            'firebase_config': get_firebase_config()
                'error': 'Token Firebase manquant'
        return render(request, 'accounts/login.html', context)

        # Authentifier avec Firebase
        backend = FirebaseAuthenticationBackend()
        user = backend.authenticate(request, firebase_token=firebase_token)
def firebase_login(request):
        if user:
    Connecte un utilisateur avec un token Firebase
            login(request, user, backend='accounts.firebase_auth.FirebaseAuthenticationBackend')

            logger.info(f"Connexion Firebase réussie pour {user.email}")

                'success': True,
                'message': 'Connexion réussie',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.full_name,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Échec de l\'authentification'
            }, status=401)
            logger.info(f"Connexion Firebase réussie pour {user.email}")
        logger.error(f"Erreur lors de la connexion Firebase: {e}")
        return JsonResponse({
            'success': False,
                'message': 'Connexion réussie',


@csrf_exempt
@require_http_methods(["POST"])
def firebase_logout(request):
    """
    Déconnecte l'utilisateur
    """
    try:
        # Note: La révocation des tokens Firebase nécessiterait une fonction spécifique
        # Pour l'instant, on fait juste la déconnexion Django

            logger.info(f"Déconnexion Firebase pour {request.user.email}")

        logout(request)

        return JsonResponse({
            'success': True,
            'message': 'Déconnexion réussie'
        })
        logger.error(f"Erreur lors de la connexion Firebase: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion Firebase: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la déconnexion'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
    Déconnecte l'utilisateur
    """
    Vérifie un token Firebase sans connecter l'utilisateur
        # Note: La révocation des tokens Firebase nécessiterait une fonction spécifique
        # Pour l'instant, on fait juste la déconnexion Django
    """
            logger.info(f"Déconnexion Firebase pour {request.user.email}")

        logout(request)

        return JsonResponse({
            'success': True,
            'message': 'Déconnexion réussie'
        })

    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion Firebase: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la déconnexion'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_token_view(request):
    """
    Vérifie un token Firebase sans connecter l'utilisateur
    """
    try:
        data = json.loads(request.body)
        firebase_token = data.get('idToken')

        if not firebase_token:
            return JsonResponse({
                'success': False,
                'error': 'Token Firebase manquant'
            }, status=400)


        decoded_token = verify_firebase_token(firebase_token)

        if decoded_token:

        # Vérifier le token
                'token_info': {
                    'uid': decoded_token.get('uid'),
                    'email': decoded_token.get('email'),
                    'email_verified': decoded_token.get('email_verified'),
                    'name': decoded_token.get('name'),
                    'picture': decoded_token.get('picture'),
                }
        if decoded_token:
        else:
            return JsonResponse({
                'success': False,
                'error': 'Token invalide'
            }, status=401)
            return JsonResponse({
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
                'success': True,
        logger.error(f"Erreur lors de la vérification du token: {e}")
                    'uid': decoded_token.get('uid'),
                    'email': decoded_token.get('email'),
            'error': 'Erreur interne du serveur'
                    'name': decoded_token.get('name'),
                    'picture': decoded_token.get('picture'),
                }
@login_required
            })
    """
    Affiche le profil utilisateur avec les informations Firebase
    """

        'user': request.user,
        'has_firebase_uid': hasattr(request.user, 'firebase_uid') and request.user.firebase_uid,
        'firebase_config': get_firebase_config()  # Ajout pour les fonctionnalités Firebase
            'success': False,
    return render(request, 'accounts/profile.html', context)
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {e}")
        return JsonResponse({
def link_firebase_account(request):
    """
    Lie un compte Firebase existant à un compte Django
    """
        }, status=500)


            'error': 'Utilisateur non authentifié'
def firebase_profile(request):
    """
    Affiche le profil utilisateur avec les informations Firebase
    """
        firebase_token = data.get('idToken')

        if not firebase_token:
            return JsonResponse({
                'success': False,
                'error': 'Token Firebase manquant'
            }, status=400)

        # Vérifier le token Firebase
        decoded_token = verify_firebase_token(firebase_token)

        if not decoded_token:
            return JsonResponse({
                'success': False,
                'error': 'Token Firebase invalide'
            }, status=401)

        # Lier le compte Firebase à l'utilisateur Django
    context = {
        firebase_uid = decoded_token.get('uid')
        'user': request.user,
        if hasattr(user, 'firebase_uid'):
            user.firebase_uid = firebase_uid
            user.save()

            logger.info(f"Compte Firebase lié pour {user.email}")

            return JsonResponse({
                'success': True,
                'message': 'Compte Firebase lié avec succès'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Le modèle utilisateur ne supporte pas Firebase UID'
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'

                'success': False,
        logger.error(f"Erreur lors de la liaison du compte Firebase: {e}")
            }, status=400)

            'error': 'Erreur interne du serveur'
        decoded_token = verify_firebase_token(firebase_token)


def firebase_auth_status(request):
    """
    Retourne le statut d'authentification Firebase de l'utilisateur
    """
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'full_name': request.user.full_name,
            },
            'has_firebase_uid': hasattr(request.user, 'firebase_uid') and bool(request.user.firebase_uid),
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'user': None,
            'has_firebase_uid': False,
        })


class SocialAuthCallbackView(View):
    """
    Vue de callback pour les authentifications sociales (Google, Facebook)
    Cette vue sera appelée après la redirection depuis les providers sociaux
    """

    def get(self, request):
        """Gère les callbacks des providers sociaux"""
        provider = request.GET.get('provider', '')
        success = request.GET.get('success', 'false').lower() == 'true'

        if success:
            messages.success(request, f'Connexion {provider} réussie!')
            return redirect('store:index')
        else:
            error_message = request.GET.get('error', 'Erreur d\'authentification')
            messages.error(request, f'Erreur de connexion {provider}: {error_message}')
            return redirect('accounts:login')


def firebase_config_view(request):
    """
    Retourne la configuration Firebase pour le frontend
    """
    config = {
        'apiKey': getattr(settings, 'FIREBASE_API_KEY', ''),
        'authDomain': getattr(settings, 'FIREBASE_AUTH_DOMAIN', ''),
        'projectId': getattr(settings, 'FIREBASE_PROJECT_ID', ''),
        'storageBucket': getattr(settings, 'FIREBASE_STORAGE_BUCKET', ''),
        'messagingSenderId': getattr(settings, 'FIREBASE_MESSAGING_SENDER_ID', ''),
        'appId': getattr(settings, 'FIREBASE_APP_ID', ''),
    }

    return JsonResponse({'firebase_config': config})

        if not decoded_token:

                'success': False,
                'error': 'Token Firebase invalide'
            }, status=401)

        # Lier le compte Firebase à l'utilisateur Django
        user = request.user
        firebase_uid = decoded_token.get('uid')

        if hasattr(user, 'firebase_uid'):

            user.save()

            logger.info(f"Compte Firebase lié pour {user.email}")

            return JsonResponse({
                'success': True,
                'message': 'Compte Firebase lié avec succès'
            })
        else:

                'success': False,
                'error': 'Le modèle utilisateur ne supporte pas Firebase UID'
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de la liaison du compte Firebase: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=500)


def firebase_auth_status(request):
    """
    Retourne le statut d'authentification Firebase de l'utilisateur
    """
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'full_name': request.user.full_name,
            },
            'has_firebase_uid': hasattr(request.user, 'firebase_uid') and bool(request.user.firebase_uid),
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'user': None,
            'has_firebase_uid': False,
        })


class SocialAuthCallbackView(View):

    Vue de callback pour les authentifications sociales (Google, Facebook)
    Cette vue sera appelée après la redirection depuis les providers sociaux
    """


        """Gère les callbacks des providers sociaux"""
        provider = request.GET.get('provider', '')
        success = request.GET.get('success', 'false').lower() == 'true'

        if success:
            messages.success(request, f'Connexion {provider} réussie!')
            return redirect('store:index')
        else:
            error_message = request.GET.get('error', 'Erreur d\'authentification')
            messages.error(request, f'Erreur de connexion {provider}: {error_message}')
            return redirect('accounts:login')


def firebase_config_view(request):
    """
    Retourne la configuration Firebase pour le frontend
    """
    config = {
        'apiKey': getattr(settings, 'FIREBASE_API_KEY', ''),
        'authDomain': getattr(settings, 'FIREBASE_AUTH_DOMAIN', ''),
        'projectId': getattr(settings, 'FIREBASE_PROJECT_ID', ''),

        'messagingSenderId': getattr(settings, 'FIREBASE_MESSAGING_SENDER_ID', ''),
        'appId': getattr(settings, 'FIREBASE_APP_ID', ''),
    }

    return JsonResponse({'firebase_config': config})
