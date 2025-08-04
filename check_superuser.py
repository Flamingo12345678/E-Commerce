#!/usr/bin/env python
"""
Script pour vérifier les super utilisateurs dans la base de données PostgreSQL
"""
import os
import django
import sys

# Configuration de Django
sys.path.append('/Users/flamingo/PycharmProjects/E-Commerce')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.contrib.auth.models import User

def check_superusers():
    """Affiche tous les super utilisateurs de la base de données"""
    try:
        superusers = User.objects.filter(is_superuser=True)

        if superusers.exists():
            print("=== SUPER UTILISATEURS TROUVÉS ===")
            print("-" * 50)

            for user in superusers:
                print(f"ID: {user.id}")
                print(f"Nom d'utilisateur: {user.username}")
                print(f"Email: {user.email}")
                print(f"Prénom: {user.first_name}")
                print(f"Nom: {user.last_name}")
                print(f"Actif: {user.is_active}")
                print(f"Staff: {user.is_staff}")
                print(f"Super utilisateur: {user.is_superuser}")
                print(f"Date de création: {user.date_joined}")
                print(f"Dernière connexion: {user.last_login}")
                print("-" * 50)
        else:
            print("❌ Aucun super utilisateur trouvé dans la base de données")

        # Afficher aussi tous les utilisateurs staff
        staff_users = User.objects.filter(is_staff=True)
        if staff_users.exists():
            print("\n=== UTILISATEURS STAFF ===")
            print("-" * 50)
            for user in staff_users:
                print(f"ID: {user.id}")
                print(f"Nom d'utilisateur: {user.username}")
                print(f"Email: {user.email}")
                print(f"Super utilisateur: {user.is_superuser}")
                print("-" * 25)

    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

    return True

if __name__ == "__main__":
    print("🔍 Vérification des super utilisateurs...")
    success = check_superusers()

    if not success:
        print("\n💡 Suggestion: Créez un super utilisateur avec:")
        print("python manage.py createsuperuser")
