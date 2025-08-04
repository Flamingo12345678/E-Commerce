from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Affiche tous les super utilisateurs de la base de données'

    def handle(self, *args, **options):
        try:
            # Récupérer tous les super utilisateurs
            superusers = User.objects.filter(is_superuser=True)

            if superusers.exists():
                self.stdout.write(self.style.SUCCESS('=== SUPER UTILISATEURS TROUVÉS ==='))
                self.stdout.write('-' * 50)

                for user in superusers:
                    self.stdout.write(f'ID: {user.id}')
                    self.stdout.write(f'Nom d\'utilisateur: {user.username}')
                    self.stdout.write(f'Email: {user.email}')
                    self.stdout.write(f'Prénom: {user.first_name}')
                    self.stdout.write(f'Nom: {user.last_name}')
                    self.stdout.write(f'Actif: {user.is_active}')
                    self.stdout.write(f'Staff: {user.is_staff}')
                    self.stdout.write(f'Date de création: {user.date_joined}')
                    self.stdout.write(f'Dernière connexion: {user.last_login}')
                    self.stdout.write('-' * 50)

                self.stdout.write(self.style.SUCCESS(f'Total: {superusers.count()} super utilisateur(s)'))
            else:
                self.stdout.write(self.style.WARNING('❌ Aucun super utilisateur trouvé'))
                self.stdout.write('Vous pouvez en créer un avec:')
                self.stdout.write('python manage.py createsuperuser')

            # Afficher aussi les utilisateurs staff
            staff_users = User.objects.filter(is_staff=True, is_superuser=False)
            if staff_users.exists():
                self.stdout.write('\n=== UTILISATEURS STAFF (non super) ===')
                for user in staff_users:
                    self.stdout.write(f'ID: {user.id}, Username: {user.username}, Email: {user.email}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}'))
