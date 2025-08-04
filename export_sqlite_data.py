#!/usr/bin/env python
"""
Script pour exporter les données de SQLite vers un format compatible PostgreSQL
"""
import os
import sys
import json
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

import django
django.setup()

from django.core import serializers
from django.apps import apps
from django.contrib.auth.models import User, Group, Permission
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

def export_data():
    """Exporte toutes les données des modèles vers un fichier JSON"""

    # Liste des modèles à exporter (dans l'ordre des dépendances)
    models_to_export = [
        # Modèles Django de base
        ContentType,
        Permission,
        Group,
        User,

        # Modèles store
        Category,
        Product,
        ProductVariant,

        # Modèles accounts (utilisateurs d'abord)
        Shopper,
        Address,
        PaymentMethod,

        # Modèles avec relations
        Cart,
        Order,
        Wishlist,
        Transaction,
        OrphanTransaction,

        # Modèles factures
        InvoiceTemplate,
        RecurringInvoiceTemplate,
        Invoice,
        InvoiceItem,
        InvoicePayment,
        InvoiceReminder,

        # Logs
        WebhookLog,
        LogEntry,
        Session,
    ]

    all_data = []

    for model in models_to_export:
        try:
            queryset = model.objects.all()
            count = queryset.count()

            if count > 0:
                print(f"Exportation de {count} enregistrements de {model._meta.label}")

                # Sérialiser les données
                serialized_data = serializers.serialize('json', queryset)
                model_data = json.loads(serialized_data)
                all_data.extend(model_data)
            else:
                print(f"Aucun enregistrement trouvé pour {model._meta.label}")

        except Exception as e:
            print(f"Erreur lors de l'exportation de {model._meta.label}: {e}")
            continue

    # Sauvegarder dans un fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sqlite_data_export_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\nExportation terminée!")
    print(f"Fichier créé: {filename}")
    print(f"Total d'objets exportés: {len(all_data)}")

    return filename

if __name__ == "__main__":
    # Temporairement changer la configuration pour utiliser SQLite
    from django.conf import settings

    # Sauvegarder la configuration actuelle
    original_databases = settings.DATABASES.copy()

    # Configurer pour utiliser SQLite
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/Users/flamingo/PycharmProjects/E-Commerce/db.sqlite3',
        }
    }

    # Réinitialiser les connexions
    from django.db import connections
    for conn in connections.all():
        conn.close()

    try:
        filename = export_data()
        print(f"\nDonnées exportées avec succès dans: {filename}")
    except Exception as e:
        print(f"Erreur lors de l'exportation: {e}")
        sys.exit(1)
    finally:
        # Restaurer la configuration PostgreSQL
        settings.DATABASES = original_databases
        for conn in connections.all():
            conn.close()
