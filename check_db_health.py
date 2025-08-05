#!/usr/bin/env python3
"""
Script de vérification de la santé de la base de données
"""
import os
import sys
import django
from django.conf import settings
from django.db import connections
from django.core.management.base import BaseCommand

# Configuration du chemin Django
sys.path.append('/Users/flamingo/PycharmProjects/E-Commerce')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

def check_database_connections():
    """Vérifier l'état des connexions à la base de données"""
    try:
        db_conn = connections['default']
        
        # Tester la connexion
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        print("✅ Connexion à la base de données OK")
        print(f"Database: {db_conn.settings_dict['NAME']}")
        print(f"Host: {db_conn.settings_dict['HOST']}")
        print(f"Port: {db_conn.settings_dict['PORT']}")
        
        # Vérifier le nombre de connexions actives
        with db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            active_connections = cursor.fetchone()[0]
            print(f"Connexions actives: {active_connections}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False

def close_idle_connections():
    """Fermer les connexions inactives"""
    try:
        from django.db import connections
        for conn in connections.all():
            conn.close()
        print("✅ Connexions fermées")
    except Exception as e:
        print(f"❌ Erreur lors de la fermeture des connexions: {e}")

if __name__ == "__main__":
    print("=== Vérification de la santé de la base de données ===")
    if check_database_connections():
        print("Base de données opérationnelle")
    else:
        print("Problème détecté avec la base de données")
        close_idle_connections()
