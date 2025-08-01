#!/usr/bin/env python
"""
Script de test robuste pour le projet E-Commerce.
Ce script configure l'environnement et exécute tous les tests de manière sécurisée.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_test_environment():
    """Configure l'environnement de test"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.test_settings')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    os.environ.setdefault('TESTING', 'True')
    os.environ.setdefault('DEBUG', 'False')
    os.environ.setdefault('SECRET_KEY', 'test-secret-key')
    os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')
    os.environ.setdefault('EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend')

    # Désactiver Firebase pour les tests
    os.environ.setdefault('FIREBASE_API_KEY', 'test-key')
    os.environ.setdefault('FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com')
    os.environ.setdefault('FIREBASE_PROJECT_ID', 'test-project')

    # Configurations de paiement factices
    os.environ.setdefault('STRIPE_PUBLISHABLE_KEY', 'pk_test_fake')
    os.environ.setdefault('STRIPE_SECRET_KEY', 'sk_test_fake')
    os.environ.setdefault('STRIPE_WEBHOOK_SECRET', 'whsec_test_fake')

    django.setup()

def run_tests():
    """Exécute tous les tests"""
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)

    # Exécuter les tests par application pour éviter les conflits
    apps_to_test = ['store', 'accounts', 'pages']

    for app in apps_to_test:
        print(f"\n{'='*50}")
        print(f"Tests pour l'application: {app}")
        print(f"{'='*50}")

        try:
            failures = test_runner.run_tests([app])
            if failures:
                print(f"ÉCHEC: {failures} test(s) ont échoué pour {app}")
            else:
                print(f"SUCCÈS: Tous les tests de {app} ont réussi")
        except Exception as e:
            print(f"ERREUR lors des tests de {app}: {e}")

    print(f"\n{'='*50}")
    print("Tests terminés")
    print(f"{'='*50}")

if __name__ == '__main__':
    setup_test_environment()
    run_tests()
