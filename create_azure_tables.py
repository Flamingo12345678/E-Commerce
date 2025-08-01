#!/usr/bin/env python
"""
Script pour créer les tables Django sur Azure MySQL et importer les données
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

# Configuration pour se connecter à Azure MySQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

# Configuration spéciale pour Azure MySQL
os.environ['DB_HOST'] = 'flam-server.mysql.database.azure.com'
os.environ['DB_NAME'] = 'ecommerce_db'
os.environ['DB_USER'] = 'Flamingo'
os.environ['DB_PASSWORD'] = 'Fl@mingo_237*'
os.environ['DB_PORT'] = '3306'

# Options SSL nécessaires pour Azure MySQL
os.environ['DATABASE_OPTIONS'] = '{"ssl": {"ssl_disabled": false}, "init_command": "SET sql_mode=\'STRICT_TRANS_TABLES\'"}'

# Configurer Django
django.setup()

def create_tables():
    """Créer les tables Django sur Azure MySQL"""
    print("🚀 Création des tables Django sur Azure MySQL...")

    try:
        # Exécuter les migrations
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("✅ Tables Django créées avec succès sur Azure MySQL!")
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        print("Essayons une approche alternative...")

        # Essayer avec manage.py directement
        os.system('python manage.py migrate --run-syncdb')

if __name__ == '__main__':
    create_tables()
