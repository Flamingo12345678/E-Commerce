"""
🚀 COMMANDE DE TEST POUR LE SYSTÈME DE NOTIFICATIONS
==================================================

Cette commande teste tous les aspects du système de notifications.
Usage: python manage.py test_notification_system
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.email_services import EmailService
from accounts.models import Shopper
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Teste le système de notifications complet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email de test pour recevoir les notifications'
        )
        parser.add_argument(
            '--skip-emails',
            action='store_true',
            help='Tester sans envoyer réellement les emails'
        )

    def handle(self, *args, **options):
        test_email = options.get('email')
        skip_emails = options.get('skip_emails', False)

        self.stdout.write(
            self.style.SUCCESS("🧪 DÉMARRAGE DES TESTS DU SYSTÈME DE NOTIFICATIONS")
        )

        # Test 1: Configuration email
        self.test_email_configuration()

        # Test 2: Service d'email
        self.test_email_service(test_email, skip_emails)

        # Test 3: Templates
        self.test_email_templates()

        # Test 4: Base de données
        self.test_database_integration()

        # Test 5: Commande newsletter
        self.test_newsletter_command()

        self.stdout.write(
            self.style.SUCCESS("✅ TOUS LES TESTS SONT TERMINÉS !")
        )

    def test_email_configuration(self):
        """Teste la configuration email"""
        self.stdout.write("📧 Test de la configuration email...")

        required_settings = [
            'EMAIL_BACKEND',
            'EMAIL_HOST',
            'EMAIL_PORT',
            'DEFAULT_FROM_EMAIL'
        ]

        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)

        if missing_settings:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Paramètres manquants: {missing_settings}")
            )
        else:
            self.stdout.write(self.style.SUCCESS("✅ Configuration email OK"))

        # Affichage de la configuration actuelle
        self.stdout.write(f"   Backend: {getattr(settings, 'EMAIL_BACKEND', 'Non configuré')}")
        self.stdout.write(f"   Host: {getattr(settings, 'EMAIL_HOST', 'Non configuré')}")
        self.stdout.write(f"   From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Non configuré')}")

    def test_email_service(self, test_email=None, skip_emails=False):
        """Teste le service d'email"""
        self.stdout.write("🔧 Test du service EmailService...")

        # Vérifier que la classe existe
        try:
            from accounts.email_services import EmailService
            self.stdout.write(self.style.SUCCESS("✅ EmailService importé"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur import EmailService: {e}"))
            return

        # Vérifier les méthodes
        required_methods = [
            'send_order_confirmation',
            'send_order_status_update',
            'send_newsletter',
            'send_welcome_email'
        ]

        for method in required_methods:
            if hasattr(EmailService, method):
                self.stdout.write(f"   ✅ Méthode {method} disponible")
            else:
                self.stdout.write(f"   ❌ Méthode {method} manquante")

        # Test d'envoi si email fourni
        if test_email and not skip_emails:
            self.stdout.write(f"📤 Test d'envoi d'email vers {test_email}...")
            try:
                # Créer un utilisateur de test temporaire
                test_user = User(
                    username='test_notifications',
                    email=test_email,
                    first_name='Test',
                    last_name='User'
                )

                # Tester l'email de bienvenue
                result = EmailService.send_welcome_email(test_user)

                if result:
                    self.stdout.write(self.style.SUCCESS("✅ Email de test envoyé !"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Email non envoyé (préférences?)"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur envoi test: {e}"))

    def test_email_templates(self):
        """Teste l'existence des templates d'email"""
        self.stdout.write("📄 Test des templates d'email...")

        from django.template.loader import get_template
        from django.template import TemplateDoesNotExist

        templates = [
            'emails/order_confirmation.html',
            'emails/order_status_update.html',
            'emails/newsletter.html',
            'emails/welcome.html'
        ]

        for template_name in templates:
            try:
                template = get_template(template_name)
                self.stdout.write(f"   ✅ Template {template_name} trouvé")
            except TemplateDoesNotExist:
                self.stdout.write(f"   ❌ Template {template_name} manquant")

    def test_database_integration(self):
        """Teste l'intégration avec la base de données"""
        self.stdout.write("🗄️  Test de l'intégration base de données...")

        # Test du modèle Shopper
        try:
            total_users = Shopper.objects.count()
            newsletter_subscribers = Shopper.objects.filter(
                newsletter_subscription=True,
                email_notifications=True
            ).count()

            self.stdout.write(f"   ✅ Utilisateurs total: {total_users}")
            self.stdout.write(f"   ✅ Abonnés newsletter: {newsletter_subscribers}")

            # Vérifier les champs nécessaires
            required_fields = ['email_notifications', 'newsletter_subscription']
            sample_user = Shopper.objects.first()

            if sample_user:
                for field in required_fields:
                    if hasattr(sample_user, field):
                        self.stdout.write(f"   ✅ Champ {field} disponible")
                    else:
                        self.stdout.write(f"   ❌ Champ {field} manquant")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur base de données: {e}"))

    def test_newsletter_command(self):
        """Teste la commande newsletter"""
        self.stdout.write("📰 Test de la commande newsletter...")

        try:
            from django.core.management import call_command
            from io import StringIO

            # Test en mode aperçu
            out = StringIO()
            call_command(
                'send_newsletter',
                'Test Newsletter',
                '<h1>Contenu de test</h1>',
                '--preview',
                stdout=out
            )

            output = out.getvalue()
            if 'APERÇU' in output:
                self.stdout.write("   ✅ Commande newsletter fonctionne (mode aperçu)")
            else:
                self.stdout.write("   ⚠️  Sortie commande inattendue")

        except Exception as e:
            self.stdout.write(f"   ❌ Erreur commande newsletter: {e}")

    def create_sample_data(self):
        """Crée des données de test si nécessaire"""
        self.stdout.write("🔧 Création de données de test...")

        # Créer un utilisateur de test s'il n'existe pas
        test_user, created = Shopper.objects.get_or_create(
            username='test_newsletter',
            defaults={
                'email': 'test@exemple.com',
                'first_name': 'Test',
                'last_name': 'Newsletter',
                'newsletter_subscription': True,
                'email_notifications': True
            }
        )

        if created:
            self.stdout.write("   ✅ Utilisateur de test créé")
        else:
            self.stdout.write("   ℹ️  Utilisateur de test existe déjà")

        return test_user
