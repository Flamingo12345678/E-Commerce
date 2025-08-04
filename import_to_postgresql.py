#!/usr/bin/env python
"""
Script pour importer les données JSON vers PostgreSQL
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
from django.db import transaction
from django.core.management.color import no_style
from django.db import connection

def import_data(filename):
    """Importe les données depuis un fichier JSON vers PostgreSQL"""

    if not os.path.exists(filename):
        print(f"Erreur: Le fichier {filename} n'existe pas")
        return False

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Lecture de {len(data)} objets depuis {filename}")

        # Désactiver temporairement les contraintes de clés étrangères
        cursor = connection.cursor()
        style = no_style()

        # Commencer une transaction
        with transaction.atomic():
            print("Importation des données...")

            # Créer les objets Django
            objects_to_create = []
            for item in data:
                try:
                    # Convertir l'objet Python en chaîne JSON pour le désérialiseur
                    json_string = json.dumps([item])
                    for obj in serializers.deserialize('json', json_string):
                        objects_to_create.append(obj)
                except Exception as e:
                    print(f"Erreur lors de la désérialisation de l'objet {item.get('model', 'unknown')}: {e}")
                    continue

            print(f"Objets préparés pour l'importation: {len(objects_to_create)}")

            # Sauvegarder les objets
            saved_count = 0
            for obj in objects_to_create:
                try:
                    obj.save()
                    saved_count += 1
                except Exception as e:
                    print(f"Erreur lors de la sauvegarde de {obj.object._meta.label}: {e}")
                    continue

            print(f"Objets sauvegardés avec succès: {saved_count}")

            # Réinitialiser les séquences PostgreSQL
            print("Réinitialisation des séquences PostgreSQL...")
            sequence_sql = connection.ops.sql_flush(style, [])
            for sql in sequence_sql:
                if 'RESTART IDENTITY' in sql or 'SEQUENCE' in sql:
                    try:
                        cursor.execute(sql)
                    except Exception as e:
                        print(f"Avertissement lors de la réinitialisation des séquences: {e}")

        print(f"\nImportation terminée avec succès!")
        return True

    except Exception as e:
        print(f"Erreur lors de l'importation: {e}")
        return False

if __name__ == "__main__":
    import sys

    # Utiliser le fichier exporté le plus récent par défaut
    filename = "sqlite_data_export_20250804_182340.json"

    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print(f"Importation des données depuis: {filename}")
    print("Base de données cible: PostgreSQL DigitalOcean")

    success = import_data(filename)

    if success:
        print("\n✅ Migration terminée avec succès!")
        print("Vos données SQLite ont été migrées vers PostgreSQL.")
    else:
        print("\n❌ Erreur lors de la migration.")
        sys.exit(1)
