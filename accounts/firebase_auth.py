"""
Module d'authentification Firebase pour l'intégration avec Django
"""

import logging
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ImproperlyConfigured
import os
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
User = get_user_model()


class FirebaseManager:
    """Gestionnaire pour l'initialisation et la gestion de Firebase"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.initialize_firebase()
            self._initialized = True
    
    def initialize_firebase(self):
        """Initialise Firebase Admin SDK"""
        try:
            # Vérifier si Firebase est déjà initialisé
            if firebase_admin._apps:
                logger.info("Firebase déjà initialisé")
                return

            # Chemin vers le fichier de service account
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)

            if cred_path and os.path.exists(cred_path):
                # Utiliser le fichier de service account
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': getattr(settings, 'FIREBASE_DATABASE_URL', None)
                })
                logger.info(f"Firebase initialisé avec le fichier de service account: {cred_path}")

            elif hasattr(settings, 'FIREBASE_CREDENTIALS_JSON'):
                # Utiliser les credentials depuis les variables d'environnement
                try:
                    cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': getattr(settings, 'FIREBASE_DATABASE_URL', None)
                    })
                    logger.info("Firebase initialisé avec les credentials JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"Erreur de parsing JSON pour les credentials Firebase: {e}")
                    raise ImproperlyConfigured(f"Credentials Firebase JSON invalides: {e}")

            else:
                # Essayer d'utiliser les credentials par défaut (pour production)
                try:
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': getattr(settings, 'FIREBASE_DATABASE_URL', None)
                    })
                    logger.info("Firebase initialisé avec les credentials par défaut")
                except Exception as e:
                    logger.warning(f"Impossible d'utiliser les credentials par défaut: {e}")
                    raise ImproperlyConfigured(
                        "Aucune configuration Firebase valide trouvée. "
                        "Veuillez configurer FIREBASE_CREDENTIALS_PATH ou FIREBASE_CREDENTIALS_JSON"
                    )

        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Firebase: {e}")
            raise ImproperlyConfigured(f"Impossible d'initialiser Firebase: {e}")

    def is_initialized(self):
        """Vérifie si Firebase est correctement initialisé"""
        return bool(firebase_admin._apps) and self._initialized


class FirebaseAuthenticationBackend(BaseBackend):
    """Backend d'authentification Django pour Firebase"""
    
    def __init__(self):
        self.firebase_manager = FirebaseManager()
    
    def authenticate(self, request, firebase_token=None, **kwargs):
        """
        Authentifie un utilisateur avec un token Firebase
        
        Args:
            request: Requête Django
            firebase_token: Token ID Firebase
            
        Returns:
            User instance ou None
        """
        if not firebase_token:
            return None
            
        if not self.firebase_manager.is_initialized():
            logger.error("Firebase n'est pas initialisé")
            return None

        try:
            # Vérifier le token Firebase
            decoded_token = auth.verify_id_token(firebase_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')
            
            if not email:
                logger.warning(f"Token Firebase sans email pour UID: {uid}")
                return None
                
            # Chercher ou créer l'utilisateur
            user = self.get_or_create_user(decoded_token)
            
            # Mettre à jour les informations utilisateur
            if user:
                self.update_user_from_firebase(user, decoded_token)
                logger.info(f"Authentification Firebase réussie pour l'utilisateur: {email}")

            return user
            
        except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError) as e:
            logger.warning(f"Token Firebase invalide ou expiré: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification Firebase: {e}")
            return None
    
    def get_or_create_user(self, decoded_token: Dict[str, Any]) -> Optional[User]:
        """
        Récupère ou crée un utilisateur à partir du token Firebase
        
        Args:
            decoded_token: Token décodé de Firebase
            
        Returns:
            User instance ou None
        """
        try:
            uid = decoded_token['uid']
            email = decoded_token.get('email')
            
            if not email:
                return None
                
            # Chercher l'utilisateur par email
            try:
                user = User.objects.get(email=email)
                # Mettre à jour le firebase_uid si nécessaire
                if hasattr(user, 'firebase_uid') and user.firebase_uid != uid:
                    user.firebase_uid = uid
                    user.save()
                return user
            except User.DoesNotExist:
                pass
                
            # Chercher par firebase_uid si disponible
            if hasattr(User, 'firebase_uid'):
                try:
                    return User.objects.get(firebase_uid=uid)
                except User.DoesNotExist:
                    pass
            
            # Créer un nouvel utilisateur
            username = email.split('@')[0]
            # S'assurer que le nom d'utilisateur est unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user_data = {
                'username': username,
                'email': email,
                'first_name': decoded_token.get('name', '').split(' ')[0] if decoded_token.get('name') else '',
                'last_name': ' '.join(decoded_token.get('name', '').split(' ')[1:]) if decoded_token.get('name') else '',
                'is_active': True,
            }
            
            # Ajouter firebase_uid si le modèle le supporte
            if hasattr(User, 'firebase_uid'):
                user_data['firebase_uid'] = uid
                
            user = User.objects.create_user(**user_data)
            logger.info(f"Nouvel utilisateur créé depuis Firebase: {email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Erreur lors de la création/récupération de l'utilisateur: {e}")
            return None
    
    def update_user_from_firebase(self, user: User, decoded_token: Dict[str, Any]):
        """
        Met à jour les informations utilisateur depuis Firebase

        Args:
            user: Instance utilisateur Django
            decoded_token: Token décodé de Firebase
        """
        try:
            updated = False
            
            # Mettre à jour le nom si disponible
            if decoded_token.get('name'):
                name_parts = decoded_token['name'].split(' ')
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                if user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                    
                if user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
            
            # Mettre à jour l'email vérifié si disponible
            if hasattr(user, 'email_verified') and 'email_verified' in decoded_token:
                email_verified = decoded_token['email_verified']
                if user.email_verified != email_verified:
                    user.email_verified = email_verified
                    updated = True

            # Sauvegarder si des modifications ont été apportées
            if updated:
                user.save()
                logger.debug(f"Informations utilisateur mises à jour depuis Firebase: {user.email}")

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur depuis Firebase: {e}")

    def get_user(self, user_id):
        """
        Récupère un utilisateur par son ID

        Args:
            user_id: ID de l'utilisateur

        Returns:
            User instance ou None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def verify_firebase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Fonction utilitaire pour vérifier un token Firebase

    Args:
        token: Token Firebase à vérifier

    Returns:
        Token décodé ou None en cas d'erreur
    """
    try:
        firebase_manager = FirebaseManager()
        if not firebase_manager.is_initialized():
            logger.error("Firebase n'est pas initialisé")
            return None

        return auth.verify_id_token(token)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token Firebase: {e}")
        return None


def get_firebase_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les informations d'un utilisateur Firebase par son UID

    Args:
        uid: UID de l'utilisateur Firebase

    Returns:
        Informations utilisateur Firebase ou None
    """
    try:
        firebase_manager = FirebaseManager()
        if not firebase_manager.is_initialized():
            logger.error("Firebase n'est pas initialisé")
            return None

        user_record = auth.get_user(uid)
        return {
            'uid': user_record.uid,
            'email': user_record.email,
            'email_verified': user_record.email_verified,
            'display_name': user_record.display_name,
            'photo_url': user_record.photo_url,
            'disabled': user_record.disabled,
        }
    except auth.UserNotFoundError:
        logger.warning(f"Utilisateur Firebase non trouvé: {uid}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'utilisateur Firebase: {e}")
        return None
