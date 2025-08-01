"""
Configuration Django pour les tests.
Ce fichier hérite de settings.py et surcharge les paramètres pour les tests.
"""

from .settings import *
import os

# Force l'utilisation de SQLite en mémoire pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        },
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Désactiver les migrations pour accélérer les tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

if os.environ.get('DISABLE_MIGRATIONS'):
    MIGRATION_MODULES = DisableMigrations()

# Configuration pour les tests
DEBUG = False
TESTING = True
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Plus rapide pour les tests
]

# Email backend pour les tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Désactiver le cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Configurations pour éviter les erreurs
SECRET_KEY = 'test-secret-key-for-testing-only'
ALLOWED_HOSTS = ['*']

# Désactiver la vérification CSRF pour les tests
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Configurations Firebase pour les tests (valeurs factices)
FIREBASE_API_KEY = 'test-api-key'
FIREBASE_AUTH_DOMAIN = 'test-domain.firebaseapp.com'
FIREBASE_PROJECT_ID = 'test-project'
FIREBASE_STORAGE_BUCKET = 'test-bucket.appspot.com'
FIREBASE_MESSAGING_SENDER_ID = '123456789'
FIREBASE_APP_ID = 'test-app-id'
FIREBASE_DATABASE_URL = 'https://test-project.firebaseio.com'
FIREBASE_CREDENTIALS_PATH = None  # Désactiver pour les tests

# Configurations de paiement pour les tests
STRIPE_PUBLISHABLE_KEY = 'pk_test_fake_key'
STRIPE_SECRET_KEY = 'sk_test_fake_key'
STRIPE_WEBHOOK_SECRET = 'whsec_test_fake'
PAYPAL_CLIENT_ID = 'test_paypal_client_id'
PAYPAL_CLIENT_SECRET = 'test_paypal_client_secret'
PAYPAL_MODE = 'sandbox'

# Désactiver les logs pendant les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
        },
        'payment': {
            'handlers': ['null'],
            'propagate': False,
        },
        'accounts.firebase_auth': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}

# Désactiver certains middlewares pour les tests si nécessaire
if os.environ.get('MINIMAL_MIDDLEWARE'):
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]
