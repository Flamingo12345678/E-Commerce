#!/usr/bin/env python
"""
Script pour examiner les données dans la base SQLite originale
"""
import os
import sys
import sqlite3

def examine_sqlite_data():
    """Examine le contenu de la base SQLite originale"""

    db_path = "/Users/flamingo/PycharmProjects/E-Commerce/db.sqlite3"

    if not os.path.exists(db_path):
        print(f"❌ Le fichier SQLite n'existe pas: {db_path}")
        return

    print("🔍 Examen de la base SQLite originale")
    print("=" * 50)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Lister toutes les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        print(f"\n📊 TABLES SQLITE ({len(tables)} tables):")
        print("-" * 40)

        total_records = 0
        tables_with_data = []

        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}];")
                count = cursor.fetchone()[0]
                print(f"{'✅' if count > 0 else '⚪'} {table_name:<35} | {count:>6} enregistrements")

                if count > 0:
                    total_records += count
                    tables_with_data.append((table_name, count))

            except Exception as e:
                print(f"❌ {table_name:<35} | Erreur: {e}")

        print(f"\n📈 RÉSUMÉ SQLite:")
        print("-" * 30)
        print(f"Total des enregistrements: {total_records}")
        print(f"Tables avec données: {len(tables_with_data)}")

        # Examiner en détail les tables avec des données
        if tables_with_data:
            print(f"\n🔍 DÉTAIL DES TABLES AVEC DONNÉES:")
            print("-" * 50)

            for table_name, count in tables_with_data:
                print(f"\n📋 Table: {table_name} ({count} enregistrements)")
                try:
                    # Obtenir les colonnes
                    cursor.execute(f"PRAGMA table_info([{table_name}]);")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]

                    # Afficher quelques échantillons
                    cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 3;")
                    rows = cursor.fetchall()

                    print(f"   Colonnes: {', '.join(column_names[:5])}{'...' if len(column_names) > 5 else ''}")

                    for i, row in enumerate(rows):
                        row_preview = str(row)[:80] + "..." if len(str(row)) > 80 else str(row)
                        print(f"   Ligne {i+1}: {row_preview}")

                except Exception as e:
                    print(f"   ❌ Erreur lors de l'examen: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ Erreur lors de la connexion à SQLite: {e}")

if __name__ == "__main__":
    examine_sqlite_data()
