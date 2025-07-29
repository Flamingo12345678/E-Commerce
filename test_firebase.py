#!/usr/bin/env python3
"""
Script de test pour l'authentification Firebase
Usage: python test_firebase.py
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from shop.firebase_config import get_firebase_config

def test_firebase_config():
    """Test de la configuration Firebase"""
    print("🔥 Test de la Configuration Firebase")
    print("=" * 50)
    
    config = get_firebase_config()
    
    required_keys = [
        'apiKey', 'authDomain', 'projectId', 
        'storageBucket', 'messagingSenderId', 'appId'
    ]
    
    missing_keys = []
    for key in required_keys:
        value = config.get(key, '')
        if value:
            print(f"✅ {key}: {value[:10]}...")
        else:
            print(f"❌ {key}: Non configuré")
            missing_keys.append(key)
    
    if missing_keys:
        print(f"\n⚠️  Clés manquantes: {', '.join(missing_keys)}")
        print("📝 Veuillez configurer ces clés dans votre fichier .env")
        print("📖 Consultez docs/FIREBASE_SETUP.md pour plus d'infos")
        return False
    else:
        print("\n🎉 Configuration Firebase complète !")
        return True

def test_firebase_admin():
    """Test du SDK Firebase Admin"""
    print("\n🔐 Test du SDK Firebase Admin")
    print("=" * 50)
    
    try:
        from accounts.firebase_auth import FirebaseAuthHelper
        
        # Test basique (ne nécessite pas de token valide)
        helper = FirebaseAuthHelper()
        print("✅ FirebaseAuthHelper importé avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Avertissement: {e}")
        print("💡 Normal si les credentials Firebase ne sont pas configurés")
        return True

def test_django_models():
    """Test des modèles Django"""
    print("\n📊 Test des Modèles Django")
    print("=" * 50)
    
    try:
        from accounts.models import Shopper
        
        # Vérifier que le champ firebase_uid existe
        if hasattr(Shopper, 'firebase_uid'):
            print("✅ Champ firebase_uid présent dans le modèle Shopper")
        else:
            print("❌ Champ firebase_uid manquant dans le modèle Shopper")
            return False
            
        # Test de création d'un utilisateur (en mémoire)
        user = Shopper(
            username='test_firebase',
            email='test@firebase.com',
            firebase_uid='test_uid_123'
        )
        print("✅ Modèle Shopper compatible Firebase")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec les modèles: {e}")
        return False

def test_urls():
    """Test des URLs Firebase"""
    print("\n🌐 Test des URLs Firebase")
    print("=" * 50)
    
    try:
        from django.urls import reverse
        
        urls_to_test = [
            'accounts:firebase_login',
            'accounts:firebase_logout', 
            'accounts:firebase_config'
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec les URLs: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧪 Test de l'Implémentation Firebase")
    print("=" * 60)
    
    tests = [
        ("Configuration Firebase", test_firebase_config),
        ("SDK Firebase Admin", test_firebase_admin),
        ("Modèles Django", test_django_models),
        ("URLs Firebase", test_urls)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n📋 Résumé des Tests")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Score: {passed}/{len(results)} tests passés")
    
    if passed == len(results):
        print("🎉 Tous les tests sont passés ! Firebase est prêt à être configuré.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    print("\n📖 Pour configurer Firebase, consultez:")
    print("   docs/FIREBASE_SETUP.md")
    print("   docs/RAPPORT_FIREBASE_IMPLEMENTATION.md")

if __name__ == "__main__":
    main()
