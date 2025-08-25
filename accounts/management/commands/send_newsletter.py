"""
Commande Django pour envoyer des newsletters
Usage: python manage.py send_newsletter "Sujet" "Contenu HTML"
"""

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from accounts.email_services import EmailService
from accounts.models import Shopper


class Command(BaseCommand):
    help = 'Envoie une newsletter aux abonnés'

    def add_arguments(self, parser):
        parser.add_argument(
            'subject',
            type=str,
            help='Sujet de la newsletter'
        )
        parser.add_argument(
            'content',
            type=str,
            help='Contenu HTML de la newsletter'
        )
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Afficher un aperçu sans envoyer'
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Envoyer uniquement à cette adresse email (pour test)'
        )

    def handle(self, *args, **options):
        subject = options['subject']
        content = options['content']
        preview = options['preview']
        test_email = options['test_email']

        # Récupérer les destinataires
        if test_email:
            # Mode test - envoyer uniquement à l'email spécifié
            try:
                recipient = Shopper.objects.get(email=test_email)
                recipients = [recipient]
                recipient_count = 1
                self.stdout.write(
                    self.style.WARNING(f"Mode test: envoi uniquement à {test_email}")
                )
            except Shopper.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Utilisateur avec l'email {test_email} non trouvé")
                )

                # Proposer de créer un utilisateur de test
                create_user = input("Voulez-vous créer un utilisateur de test ? (oui/non): ")
                if create_user.lower() in ['oui', 'o', 'yes', 'y']:
                    # Créer un utilisateur de test
                    test_user = Shopper.objects.create(
                        username=f'test_{test_email.split("@")[0]}',
                        email=test_email,
                        first_name='Test',
                        last_name='User',
                        newsletter_subscription=True,
                        email_notifications=True
                    )
                    recipients = [test_user]
                    recipient_count = 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Utilisateur de test créé: {test_email}")
                    )
                else:
                    return
        else:
            # Mode normal - tous les abonnés
            recipients = Shopper.objects.filter(
                newsletter_subscription=True,
                email_notifications=True,
                is_active=True
            )
            recipient_count = recipients.count()

        if preview:
            # Mode aperçu
            self.stdout.write(self.style.SUCCESS("=== APERÇU DE LA NEWSLETTER ==="))
            self.stdout.write(f"Sujet: {subject}")
            self.stdout.write(f"Destinataires: {recipient_count}")
            self.stdout.write("--- Contenu ---")
            self.stdout.write(content)
            self.stdout.write("--- Fin du contenu ---")
            return

        if recipient_count == 0:
            self.stdout.write(
                self.style.WARNING("Aucun destinataire trouvé pour la newsletter")
            )
            return

        # Confirmer l'envoi
        if not test_email:
            confirm = input(
                f"Êtes-vous sûr de vouloir envoyer la newsletter à {recipient_count} destinataires ? (oui/non): "
            )
            if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write(self.style.WARNING("Envoi annulé"))
                return

        # Envoyer la newsletter
        self.stdout.write(f"Envoi de la newsletter à {recipient_count} destinataire(s)...")

        sent_count, error_count = EmailService.send_newsletter(
            subject=subject,
            content=content,
            recipients=recipients
        )

        # Afficher les résultats
        self.stdout.write(
            self.style.SUCCESS(
                f"Newsletter envoyée avec succès !\n"
                f"✅ Envoyés: {sent_count}\n"
                f"❌ Erreurs: {error_count}"
            )
        )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {error_count} erreurs détectées. "
                    "Consultez les logs pour plus de détails."
                )
            )
