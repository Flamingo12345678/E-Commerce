"""
Configuration Django dédiée aux tests unitaires.
Simplifie la configuration pour éviter les problèmes de migrations.
"""

from .settings import *

# Utiliser une base de données en mémoire pour les tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Désactiver les migrations pour les tests (plus rapide)
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Configuration simplifiée pour les tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Désactiver le cache pour les tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Configuration de logging pour les tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "performance": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Désactiver les messages de debug Django
DEBUG = False

# Secret key fixe pour les tests
SECRET_KEY = "test-secret-key-for-unit-tests-only"
