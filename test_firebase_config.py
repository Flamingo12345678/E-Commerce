#!/usr/bin/env python
"""
Script de test pour vérifier la configuration Firebase
"""

import os
import sys
import django

# Ajouter le répertoire du projet au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.conf import settings
from shop.firebase_config import (
    get_firebase_config,
    is_firebase_configured,
    get_firebase_web_config,
    get_firebase_project_id,
    get_firebase_auth_domain
)
from accounts.firebase_auth import FirebaseManager
import json

def test_firebase_settings():
    """Test des paramètres Firebase dans settings.py"""
    print("=== Test des paramètres Firebase ===")

    firebase_settings = [
        'FIREBASE_API_KEY',
        'FIREBASE_AUTH_DOMAIN',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_STORAGE_BUCKET',
        'FIREBASE_MESSAGING_SENDER_ID',
        'FIREBASE_APP_ID',
        'FIREBASE_CREDENTIALS_PATH',
        'FIREBASE_DATABASE_URL'
    ]

    for setting in firebase_settings:
        value = getattr(settings, setting, None)
        status = "✓" if value else "✗"
        print(f"{status} {setting}: {'Configuré' if value else 'Non configuré'}")
        if value and len(str(value)) > 50:
            print(f"   Valeur: {str(value)[:50]}...")
        elif value:
            print(f"   Valeur: {value}")

def test_firebase_config():
    """Test de la configuration Firebase"""
    print("\n=== Test de la configuration Firebase ===")

    config = get_firebase_config()
    print(f"Configuration récupérée: {bool(config)}")

    if config:
        for key, value in config.items():
            status = "✓" if value else "✗"
            print(f"{status} {key}: {'Configuré' if value else 'Non configuré'}")

    print(f"Firebase configuré: {is_firebase_configured()}")
    print(f"Project ID: {get_firebase_project_id()}")
    print(f"Auth Domain: {get_firebase_auth_domain()}")

def test_firebase_credentials_file():
    """Test du fichier de credentials Firebase"""
    print("\n=== Test du fichier de credentials ===")

    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    print(f"Chemin des credentials: {cred_path}")

    if cred_path:
        if os.path.exists(cred_path):
            print("✓ Fichier de credentials trouvé")
            try:
                with open(cred_path, 'r') as f:
                    cred_data = json.load(f)
                    print(f"✓ Fichier JSON valide")
                    print(f"   Type: {cred_data.get('type', 'N/A')}")
                    print(f"   Project ID: {cred_data.get('project_id', 'N/A')}")
                    print(f"   Client Email: {cred_data.get('client_email', 'N/A')}")
            except json.JSONDecodeError:
                print("✗ Fichier JSON invalide")
            except Exception as e:
                print(f"✗ Erreur de lecture: {e}")
        else:
            print("✗ Fichier de credentials non trouvé")
    else:
        print("✗ Chemin des credentials non configuré")

def test_firebase_initialization():
    """Test de l'initialisation Firebase"""
    print("\n=== Test de l'initialisation Firebase ===")

    try:
        firebase_manager = FirebaseManager()
        print("✓ FirebaseManager créé")

        if firebase_manager.is_initialized():
            print("✓ Firebase initialisé avec succès")
        else:
            print("✗ Firebase non initialisé")

    except Exception as e:
        print(f"✗ Erreur d'initialisation: {e}")

def test_web_config():
    """Test de la configuration web"""
    print("\n=== Test de la configuration web ===")

    try:
        web_config = get_firebase_web_config()
        print(f"Configuration web générée: {web_config != 'null'}")

        if web_config != 'null':
            # Vérifier que c'est du JSON valide
            config_dict = json.loads(web_config)
            print("✓ Configuration web JSON valide")
            print(f"   Nombre de clés: {len(config_dict)}")
        else:
            print("✗ Configuration web non disponible")

    except Exception as e:
        print(f"✗ Erreur de configuration web: {e}")

def run_all_tests():
    """Exécute tous les tests"""
    print("🔥 TEST DE CONFIGURATION FIREBASE 🔥\n")

    test_firebase_settings()
    test_firebase_config()
    test_firebase_credentials_file()
    test_firebase_initialization()
    test_web_config()

    print("\n=== RÉSUMÉ ===")

    # Résumé global
    settings_ok = all(getattr(settings, setting, None) for setting in [
        'FIREBASE_API_KEY', 'FIREBASE_AUTH_DOMAIN', 'FIREBASE_PROJECT_ID'
    ])

    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    credentials_ok = cred_path and os.path.exists(cred_path)

    config_ok = is_firebase_configured()

    try:
        firebase_manager = FirebaseManager()
        init_ok = firebase_manager.is_initialized()
    except:
        init_ok = False

    print(f"Settings Firebase: {'✓' if settings_ok else '✗'}")
    print(f"Fichier credentials: {'✓' if credentials_ok else '✗'}")
    print(f"Configuration: {'✓' if config_ok else '✗'}")
    print(f"Initialisation: {'✓' if init_ok else '✗'}")

    if all([settings_ok, credentials_ok, config_ok, init_ok]):
        print("\n🎉 CONFIGURATION FIREBASE COMPLÈTE ET FONCTIONNELLE ! 🎉")
    else:
        print("\n❌ PROBLÈMES DÉTECTÉS DANS LA CONFIGURATION FIREBASE")
        print("Veuillez vérifier les erreurs ci-dessus.")

if __name__ == "__main__":
    run_all_tests()
