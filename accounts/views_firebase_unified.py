# -*- coding: utf-8 -*-
"""
    accounts.views_firebase_unified
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Système de connexion unifié combinant Django et Firebase
"""
import json
import logging
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.conf import settings
from django.contrib import messages
from django.views import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from .firebase_auth import (
    FirebaseAuthenticationBackend,
    verify_firebase_token
)
from .views import validate_signup_data, validate_login_data
from shop.firebase_config import get_firebase_config

logger = logging.getLogger(__name__)
User = get_user_model()


class UnifiedAuthView(View):
    """Vue unifiée pour l'authentification Django et Firebase"""

    def get(self, request):
        """Affiche la page de connexion unifiée"""
        if request.user.is_authenticated:
            return redirect('store:product_list')

        context = {
            'firebase_config': get_firebase_config(),
            'auth_mode': 'unified'
        }
        # Utiliser le template login.html existant au lieu de login_unified.html
        return render(request, 'accounts/login.html', context)

    def post(self, request):
        """Gère la connexion avec Django ou Firebase"""
        auth_type = request.POST.get('auth_type', 'django')

        if auth_type == 'firebase':
            return self._handle_firebase_auth(request)
        else:
            return self._handle_django_auth(request)

    def _handle_firebase_auth(self, request):
        """Gère l'authentification Firebase"""
        firebase_token = request.POST.get('idToken')

        if not firebase_token:
            return JsonResponse({
                'success': False,
                'error': 'Token Firebase manquant'
            }, status=400)

        try:
            backend = FirebaseAuthenticationBackend()
            user = backend.authenticate(request, firebase_token=firebase_token)

            if user:
                login(request, user, backend='accounts.firebase_auth.FirebaseAuthenticationBackend')
                logger.info(f"Connexion Firebase réussie pour {user.email}")

                return JsonResponse({
                    'success': True,
                    'message': 'Connexion réussie',
                    'redirect_url': request.GET.get('next', '/store/'),
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'full_name': user.get_full_name(),
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Échec de l\'authentification Firebase'
                }, status=401)

        except Exception as e:
            logger.error(f"Erreur lors de la connexion Firebase: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur lors de la connexion'
            }, status=500)

    def _handle_django_auth(self, request):
        """Gère l'authentification Django native"""
        # Le formulaire utilise 'username' (qui peut être email ou nom d'utilisateur)
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Debug logging
        logger.info(f"Tentative de connexion Django - Username: {username}, Password length: {len(password) if password else 0}")

        # Validation des données
        errors = validate_login_data(username, password)
        if errors:
            logger.warning(f"Erreurs de validation: {errors}")
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

        # Essayer l'authentification avec username d'abord
        user = authenticate(request, username=username, password=password)

        # Si l'authentification échoue et que l'input ressemble à un email,
        # essayer de trouver l'utilisateur par email et s'authentifier avec son username
        if not user and '@' in username:
            try:
                # Gérer le cas où plusieurs utilisateurs ont le même email
                users_by_email = User.objects.filter(email=username, is_active=True)
                user_count = users_by_email.count()

                if user_count == 0:
                    logger.warning(f"Aucun utilisateur actif trouvé avec l'email: {username}")
                elif user_count == 1:
                    user_by_email = users_by_email.first()
                    logger.info(f"Utilisateur unique trouvé par email: {user_by_email.username}")
                    user = authenticate(request, username=user_by_email.username, password=password)
                    if user:
                        logger.info(f"Authentification réussie avec username: {user_by_email.username}")
                else:
                    # Plusieurs utilisateurs avec le même email - prendre le plus récent actif
                    logger.warning(f"Plusieurs utilisateurs ({user_count}) trouvés avec l'email: {username}")
                    user_by_email = users_by_email.order_by('-date_joined').first()
                    logger.info(f"Tentative avec l'utilisateur le plus récent: {user_by_email.username}")
                    user = authenticate(request, username=user_by_email.username, password=password)
                    if user:
                        logger.info(f"Authentification réussie avec l'utilisateur le plus récent: {user_by_email.username}")

            except Exception as e:
                logger.error(f"Erreur lors de la recherche par email: {e}")

        # Debug logging
        if user:
            logger.info(f"Authentification réussie pour: {user.email}")
        else:
            logger.warning(f"Échec d'authentification pour: {username}")
            # Vérifier si l'utilisateur existe
            if '@' in username:
                user_count = User.objects.filter(email=username).count()
                logger.info(f"Nombre d'utilisateurs avec email {username}: {user_count}")
            else:
                user_exists = User.objects.filter(username=username).exists()
                logger.info(f"Utilisateur avec username {username} existe: {user_exists}")

        if user and user.is_active:
            # Spécifier explicitement le backend Django pour la connexion
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"Connexion Django réussie pour {user.email}")

            return JsonResponse({
                'success': True,
                'message': 'Connexion réussie',
                'redirect_url': request.GET.get('next', '/store/'),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.get_full_name(),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Email ou mot de passe incorrect'
            }, status=401)


class UnifiedSignupView(View):
    """Vue unifiée pour l'inscription Django et Firebase"""

    def get(self, request):
        """Affiche la page d'inscription unifiée"""
        if request.user.is_authenticated:
            return redirect('store:index')

        context = {
            'firebase_config': get_firebase_config(),
            'auth_mode': 'unified'
        }
        return render(request, 'accounts/signup_unified.html', context)

    def post(self, request):
        """Gère l'inscription avec Django ou Firebase"""
        auth_type = request.POST.get('auth_type', 'django')

        if auth_type == 'firebase':
            return self._handle_firebase_signup(request)
        else:
            return self._handle_django_signup(request)

    def _handle_firebase_signup(self, request):
        """Gère l'inscription via Firebase"""
        firebase_token = request.POST.get('idToken')

        if not firebase_token:
            return JsonResponse({
                'success': False,
                'error': 'Token Firebase manquant'
            }, status=400)

        try:
            # Vérifier le token Firebase
            decoded_token = verify_firebase_token(firebase_token)
            if not decoded_token:
                return JsonResponse({
                    'success': False,
                    'error': 'Token Firebase invalide'
                }, status=401)

            email = decoded_token.get('email')
            name = decoded_token.get('name', '')
            picture = decoded_token.get('picture')

            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(email=email).exists():
                # Connecter l'utilisateur existant
                backend = FirebaseAuthenticationBackend()
                user = backend.authenticate(request, firebase_token=firebase_token)
                if user:
                    login(request, user, backend='accounts.firebase_auth.FirebaseAuthenticationBackend')
                    return JsonResponse({
                        'success': True,
                        'message': 'Connexion réussie avec un compte existant',
                        'redirect_url': request.GET.get('next', '/store/'),
                    })

            # Créer un nouvel utilisateur
            with transaction.atomic():
                names = name.split(' ', 1)
                first_name = names[0] if names else ''
                last_name = names[1] if len(names) > 1 else ''

                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True
                )

                # Marquer comme utilisateur Firebase
                user.set_unusable_password()
                user.save()

                login(request, user, backend='accounts.firebase_auth.FirebaseAuthenticationBackend')
                logger.info(f"Inscription Firebase réussie pour {user.email}")

                return JsonResponse({
                    'success': True,
                    'message': 'Inscription réussie',
                    'redirect_url': request.GET.get('next', '/store/'),
                })

        except Exception as e:
            logger.error(f"Erreur lors de l'inscription Firebase: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur lors de l\'inscription'
            }, status=500)

    def _handle_django_signup(self, request):
        """Gère l'inscription Django native"""
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validation des données
        errors = validate_signup_data(username, email, password, password_confirm)
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=True
                )

                # Spécifier explicitement le backend Django pour l'authentification
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                logger.info(f"Inscription Django réussie pour {user.email}")

                return JsonResponse({
                    'success': True,
                    'message': 'Inscription réussie',
                    'redirect_url': request.GET.get('next', '/store/'),
                })

        except IntegrityError:
            return JsonResponse({
                'success': False,
                'error': 'Un utilisateur avec cet email existe déjà'
            }, status=400)
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription Django: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur lors de l\'inscription'
            }, status=500)


@csrf_exempt
@require_POST
def unified_logout(request):
    """Déconnexion unifiée pour Django et Firebase"""
    try:
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        logout(request)

        logger.info(f"Déconnexion unifiée pour {user_email}")

        return JsonResponse({
            'success': True,
            'message': 'Déconnexion réussie',
            'redirect_url': '/'
        })

    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion unifiée: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la déconnexion'
        }, status=500)


@login_required
def unified_profile(request):
    """Vue de profil unifiée"""
    context = {
        'user': request.user,
        'firebase_config': get_firebase_config(),
        'auth_mode': 'unified'
    }
    return render(request, 'accounts/profile_unified.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def check_auth_status(request):
    """Vérifie le statut d'authentification de l'utilisateur"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'full_name': request.user.get_full_name(),
                'has_usable_password': request.user.has_usable_password(),
            }
        })
    else:
        return JsonResponse({
            'authenticated': False
        })


@csrf_exempt
@require_http_methods(["POST"])
def link_accounts(request):
    """Lie un compte Firebase à un compte Django existant"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Utilisateur non connecté'
        }, status=401)

    try:
        data = json.loads(request.body)
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

        firebase_email = decoded_token.get('email')

        # Vérifier que l'email correspond
        if firebase_email != request.user.email:
            return JsonResponse({
                'success': False,
                'error': 'L\'email Firebase ne correspond pas au compte actuel'
            }, status=400)

        # Marquer le compte comme lié (vous pouvez ajouter un champ au modèle User)
        logger.info(f"Liaison de compte réussie pour {request.user.email}")

        return JsonResponse({
            'success': True,
            'message': 'Comptes liés avec succès'
        })

    except Exception as e:
        logger.error(f"Erreur lors de la liaison de comptes: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la liaison'
        }, status=500)
