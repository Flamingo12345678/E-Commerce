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
            if not firebase_admin._apps:
                # Chemin vers le fichier de service account
                cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
                
                if cred_path and os.path.exists(cred_path):
                    # Utiliser le fichier de service account
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialisé avec le fichier de service account")
                elif hasattr(settings, 'FIREBASE_CREDENTIALS_JSON'):
                    # Utiliser les credentials depuis les variables d'environnement
                    cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialisé avec les credentials JSON")
                else:
                    # Utiliser les credentials par défaut (pour production)
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialisé avec les credentials par défaut")
            else:
                logger.info("Firebase déjà initialisé")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Firebase: {e}")
            raise ImproperlyConfigured(f"Impossible d'initialiser Firebase: {e}")


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
                
            return user
            
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Token Firebase invalide: {e}")
            return None
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Token Firebase expiré: {e}")
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
                
            # Chercher l'utilisateur par email ou par firebase_uid
            try:
                user = User.objects.get(email=email)
                # Mettre à jour le firebase_uid si nécessaire
                if not hasattr(user, 'firebase_uid') or user.firebase_uid != uid:
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
            user_data = {
                'email': email,
                'username': email,  # Utiliser l'email comme username par défaut
                'first_name': decoded_token.get('name', '').split(' ')[0] if decoded_token.get('name') else '',
                'last_name': ' '.join(decoded_token.get('name', '').split(' ')[1:]) if decoded_token.get('name') and len(decoded_token.get('name', '').split(' ')) > 1 else '',
                'is_active': True,
            }
            
            # Ajouter firebase_uid si le modèle le supporte
            if hasattr(User, 'firebase_uid'):
                user_data['firebase_uid'] = uid
                
            user = User.objects.create_user(**user_data)
            logger.info(f"Nouvel utilisateur créé depuis Firebase: {email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return None
    
    def update_user_from_firebase(self, user: User, decoded_token: Dict[str, Any]):
        """
        Met à jour les informations de l'utilisateur à partir du token Firebase
        
        Args:
            user: Instance utilisateur Django
            decoded_token: Token décodé de Firebase
        """
        try:
            updated = False
            
            # Mettre à jour le nom si fourni
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
            
            # Mettre à jour l'email vérifié
            if decoded_token.get('email_verified') and not user.email:
                user.email = decoded_token['email']
                updated = True
            
            # Mettre à jour la photo de profil si disponible
            if decoded_token.get('picture') and hasattr(user, 'profile_picture'):
                if user.profile_picture != decoded_token['picture']:
                    user.profile_picture = decoded_token['picture']
                    updated = True
            
            if updated:
                user.save()
                logger.info(f"Informations utilisateur mises à jour: {user.email}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
    
    def get_user(self, user_id):
        """Récupère un utilisateur par son ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class FirebaseAuthHelper:
    """Classe d'aide pour l'authentification Firebase"""
    
    @staticmethod
    def verify_firebase_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie un token Firebase et retourne les informations décodées
        
        Args:
            token: Token Firebase ID
            
        Returns:
            Dict avec les informations du token ou None
        """
        try:
            firebase_manager = FirebaseManager()
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du token Firebase: {e}")
            return None
    
    @staticmethod
    def create_custom_token(uid: str, additional_claims: Optional[Dict] = None) -> Optional[str]:
        """
        Crée un token personnalisé Firebase
        
        Args:
            uid: UID de l'utilisateur Firebase
            additional_claims: Claims additionnels à inclure
            
        Returns:
            Token personnalisé ou None
        """
        try:
            firebase_manager = FirebaseManager()
            return auth.create_custom_token(uid, additional_claims)
        except Exception as e:
            logger.error(f"Erreur lors de la création du token personnalisé: {e}")
            return None
    
    @staticmethod
    def revoke_refresh_tokens(uid: str) -> bool:
        """
        Révoque tous les tokens de rafraîchissement pour un utilisateur
        
        Args:
            uid: UID de l'utilisateur Firebase
            
        Returns:
            True si succès, False sinon
        """
        try:
            firebase_manager = FirebaseManager()
            auth.revoke_refresh_tokens(uid)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la révocation des tokens: {e}")
            return False


# Initialiser Firebase au chargement du module
firebase_manager = FirebaseManager()
