# shop/firebase_config.py
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_firebase_config():
    """
    Retourne la configuration Firebase pour les templates frontend
    
    Returns:
        dict: Configuration Firebase complète
    """
    try:
        # Utiliser la configuration complète depuis les settings
        config = getattr(settings, 'FIREBASE_CONFIG', {})
        
        # Validation des clés requises
        required_keys = ['apiKey', 'authDomain', 'projectId', 'storageBucket', 'messagingSenderId', 'appId']
        missing_keys = [key for key in required_keys if not config.get(key)]
        
        if missing_keys:
            logger.warning(f"Configuration Firebase incomplète. Clés manquantes: {missing_keys}")
        
        return config
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration Firebase: {e}")
        return {}

def get_firebase_web_config():
    """
    Retourne la configuration Firebase formatée pour le web (JavaScript)
    
    Returns:
        str: Configuration Firebase au format JavaScript
    """
    config = get_firebase_config()
    if not config:
        return "null"
    
    try:
        import json
        return json.dumps(config)
    except Exception as e:
        logger.error(f"Erreur lors de la sérialisation de la configuration Firebase: {e}")
        return "null"

def is_firebase_configured():
    """
    Vérifie si Firebase est correctement configuré
    
    Returns:
        bool: True si Firebase est configuré, False sinon
    """
    config = get_firebase_config()
    required_keys = ['apiKey', 'authDomain', 'projectId']
    
    return all(config.get(key) for key in required_keys)

def get_firebase_project_id():
    """
    Retourne l'ID du projet Firebase
    
    Returns:
        str: ID du projet Firebase ou chaîne vide
    """
    return getattr(settings, 'FIREBASE_PROJECT_ID', '')

def get_firebase_auth_domain():
    """
    Retourne le domaine d'authentification Firebase
    
    Returns:
        str: Domaine d'authentification Firebase ou chaîne vide
    """
    return getattr(settings, 'FIREBASE_AUTH_DOMAIN', '')

# Configuration Firebase pour rétrocompatibilité
FIREBASE_CONFIG = get_firebase_config()
