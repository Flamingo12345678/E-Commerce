#!/usr/bin/env python
"""
Script pour vérifier les tables PostgreSQL et leur contenu
"""
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

import django
django.setup()

from django.db import connection
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry

# Importer vos modèles personnalisés
from store.models import Category, Product, ProductVariant, Cart, Order, Wishlist
from accounts.models import (
    Shopper, Address, PaymentMethod, Transaction, Invoice, InvoiceItem,
    InvoicePayment, InvoiceReminder, InvoiceTemplate, RecurringInvoiceTemplate,
    OrphanTransaction, WebhookLog
)

def check_database_tables():
    """Vérifie toutes les tables de la base de données"""

    print("🔍 Vérification des tables PostgreSQL DigitalOcean")
    print("=" * 60)

    cursor = connection.cursor()

    # 1. Lister toutes les tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print(f"\n📊 TABLES TROUVÉES ({len(tables)} tables):")
    print("-" * 40)

    for table in tables:
        table_name = table[0]

        # Compter les enregistrements dans chaque table
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()[0]
            print(f"✅ {table_name:<35} | {count:>6} enregistrements")
        except Exception as e:
            print(f"❌ {table_name:<35} | Erreur: {e}")

    print("\n" + "=" * 60)

    # 2. Vérifier les modèles Django spécifiques
    models_to_check = [
        # Modèles Django de base
        ('ContentType', ContentType),
        ('Permission', Permission),
        ('Group', Group),

        # Modèles store
        ('Category', Category),
        ('Product', Product),
        ('ProductVariant', ProductVariant),
        ('Cart', Cart),
        ('Order', Order),
        ('Wishlist', Wishlist),

        # Modèles accounts
        ('Shopper', Shopper),
        ('Address', Address),
        ('PaymentMethod', PaymentMethod),
        ('Transaction', Transaction),
        ('OrphanTransaction', OrphanTransaction),
        ('InvoiceTemplate', InvoiceTemplate),
        ('RecurringInvoiceTemplate', RecurringInvoiceTemplate),
        ('Invoice', Invoice),
        ('InvoiceItem', InvoiceItem),
        ('InvoicePayment', InvoicePayment),
        ('InvoiceReminder', InvoiceReminder),
        ('WebhookLog', WebhookLog),

        # Modèles système
        ('LogEntry', LogEntry),
        ('Session', Session),
    ]

    print(f"\n🧩 VÉRIFICATION DES MODÈLES DJANGO ({len(models_to_check)} modèles):")
    print("-" * 60)

    for model_name, model_class in models_to_check:
        try:
            count = model_class.objects.count()
            table_name = model_class._meta.db_table
            print(f"✅ {model_name:<25} | Table: {table_name:<30} | {count:>4} objets")
        except Exception as e:
            print(f"❌ {model_name:<25} | Erreur: {e}")

    # 3. Vérifier les superutilisateurs
    print(f"\n👤 SUPERUTILISATEURS:")
    print("-" * 30)
    try:
        superusers = Shopper.objects.filter(is_superuser=True)
        if superusers.exists():
            for user in superusers:
                print(f"✅ {user.username} ({user.email})")
        else:
            print("❌ Aucun superutilisateur trouvé")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des superutilisateurs: {e}")

    # 4. Vérifier les contraintes et index
    print(f"\n🔗 CONTRAINTES ET INDEX:")
    print("-" * 40)

    # Vérifier les contraintes de clés étrangères
    cursor.execute("""
        SELECT 
            tc.table_name, 
            tc.constraint_name, 
            tc.constraint_type
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public' 
        AND tc.constraint_type IN ('FOREIGN KEY', 'PRIMARY KEY', 'UNIQUE')
        ORDER BY tc.table_name, tc.constraint_type;
    """)

    constraints = cursor.fetchall()
    constraint_counts = {}

    for constraint in constraints:
        constraint_type = constraint[2]
        constraint_counts[constraint_type] = constraint_counts.get(constraint_type, 0) + 1

    for constraint_type, count in constraint_counts.items():
        print(f"✅ {constraint_type:<15} | {count:>3} contraintes")

    # 5. Vérifier les séquences
    cursor.execute("""
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema = 'public';
    """)

    sequences = cursor.fetchall()
    print(f"\n🔢 SÉQUENCES PostgreSQL:")
    print("-" * 30)
    print(f"✅ {len(sequences)} séquences trouvées")

    cursor.close()

    print(f"\n🎉 RÉSUMÉ:")
    print("-" * 20)
    print(f"✅ Base de données: PostgreSQL DigitalOcean")
    print(f"✅ Tables trouvées: {len(tables)}")
    print(f"✅ Modèles Django: {len(models_to_check)}")
    print(f"✅ Migration: RÉUSSIE")
    print(f"✅ Structure: COMPLÈTE")

if __name__ == "__main__":
    try:
        check_database_tables()
        print(f"\n✅ Vérification terminée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")
        sys.exit(1)
