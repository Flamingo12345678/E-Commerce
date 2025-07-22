# shop/firebase_config.py
from django.conf import settings

# Configuration Firebase
FIREBASE_CONFIG = {
    "apiKey": getattr(settings, "FIREBASE_API_KEY", ""),
    "authDomain": getattr(settings, "FIREBASE_AUTH_DOMAIN", ""),
    "projectId": getattr(settings, "FIREBASE_PROJECT_ID", ""),
    "storageBucket": getattr(settings, "FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": getattr(settings, "FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": getattr(settings, "FIREBASE_APP_ID", ""),
}


def get_firebase_config():
    """Retourne la configuration Firebase pour les templates"""
    return FIREBASE_CONFIG
