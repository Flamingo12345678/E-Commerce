from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Vérifie la configuration de la base de données et affiche les informations de connexion'

    def handle(self, *args, **options):
        try:
            # Afficher la configuration de la base de données
            db_config = settings.DATABASES['default']

            self.stdout.write(self.style.SUCCESS('=== CONFIGURATION BASE DE DONNÉES ==='))
            self.stdout.write(f"Engine: {db_config.get('ENGINE', 'Non défini')}")
            self.stdout.write(f"Name: {db_config.get('NAME', 'Non défini')}")
            self.stdout.write(f"Host: {db_config.get('HOST', 'Non défini')}")
            self.stdout.write(f"Port: {db_config.get('PORT', 'Non défini')}")
            self.stdout.write(f"User: {db_config.get('USER', 'Non défini')}")

            # Vérifier les variables d'environnement
            self.stdout.write('\n=== VARIABLES D\'ENVIRONNEMENT ===')
            database_url = os.environ.get('DATABASE_URL', 'Non définie')
            if database_url != 'Non définie':
                # Masquer le mot de passe pour la sécurité
                if 'postgres://' in database_url or 'postgresql://' in database_url:
                    parts = database_url.split('@')
                    if len(parts) > 1:
                        host_part = parts[1]
                        self.stdout.write(f"DATABASE_URL Host: {host_part}")
                        if 'digitalocean' in host_part or 'db.ondigitalocean.com' in host_part:
                            self.stdout.write(self.style.SUCCESS('✅ Base DigitalOcean détectée'))
                        elif 'heroku' in host_part or 'amazonaws.com' in host_part:
                            self.stdout.write(self.style.WARNING('⚠️  Base Heroku/AWS détectée'))
                        else:
                            self.stdout.write(f'Base externe: {host_part}')
                else:
                    self.stdout.write(f"DATABASE_URL: {database_url[:50]}...")
            else:
                self.stdout.write("DATABASE_URL: Non définie")

            # Tester la connexion
            self.stdout.write('\n=== TEST DE CONNEXION ===')
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    self.stdout.write(f"Version PostgreSQL: {version}")

                    # Compter les utilisateurs
                    cursor.execute("SELECT COUNT(*) FROM auth_user;")
                    user_count = cursor.fetchone()[0]
                    self.stdout.write(f"Nombre total d'utilisateurs: {user_count}")

                    # Compter les super utilisateurs
                    cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_superuser = true;")
                    superuser_count = cursor.fetchone()[0]
                    self.stdout.write(f"Nombre de super utilisateurs: {superuser_count}")

                    if superuser_count > 0:
                        cursor.execute("SELECT id, username, email FROM auth_user WHERE is_superuser = true;")
                        superusers = cursor.fetchall()
                        self.stdout.write('\n=== SUPER UTILISATEURS ===')
                        for user in superusers:
                            self.stdout.write(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")

                self.stdout.write(self.style.SUCCESS('✅ Connexion à la base de données réussie'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erreur de connexion: {e}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur générale: {e}'))
