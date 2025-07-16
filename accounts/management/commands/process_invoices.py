"""
Commande de gestion pour traiter les factures récurrentes et les rappels
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.invoice_models import RecurringInvoiceTemplate, Invoice, InvoiceReminder
from accounts.invoice_services import InvoiceManager
import logging

logger = logging.getLogger("payment")


class Command(BaseCommand):
    help = "Traite les factures récurrentes et envoie les rappels"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule l'exécution sans créer de factures",
        )
        parser.add_argument(
            "--recurring-only",
            action="store_true",
            help="Traite uniquement les factures récurrentes",
        )
        parser.add_argument(
            "--reminders-only",
            action="store_true",
            help="Traite uniquement les rappels",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        recurring_only = options["recurring_only"]
        reminders_only = options["reminders_only"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Mode simulation activé - aucune action réelle")
            )

        if not reminders_only:
            self.process_recurring_invoices(dry_run)

        if not recurring_only:
            self.process_reminders(dry_run)

    def process_recurring_invoices(self, dry_run=False):
        """
        Traite les factures récurrentes qui doivent être générées
        """
        self.stdout.write("Traitement des factures récurrentes...")

        templates = RecurringInvoiceTemplate.objects.filter(is_active=True)

        generated_count = 0

        for template in templates:
            if template.should_generate_invoice():
                self.stdout.write(f"Génération de facture pour: {template.name}")

                if not dry_run:
                    try:
                        invoice = template.generate_invoice()
                        if invoice:
                            generated_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Facture {invoice.invoice_number} créée"
                                )
                            )

                            # Envoyer automatiquement si configuré
                            if template.auto_send:
                                invoice_manager = InvoiceManager()
                                if invoice_manager.send_invoice_with_provider(
                                    invoice, "stripe"
                                ):
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"✓ Facture {invoice.invoice_number} envoyée"
                                        )
                                    )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Erreur lors de la génération: {e}")
                        )
                        logger.error(f"Erreur génération facture récurrente: {e}")
                else:
                    generated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[SIMULATION] Facture générée pour {template.name}"
                        )
                    )

        if generated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n{generated_count} facture(s) récurrente(s) traitée(s)"
                )
            )
        else:
            self.stdout.write("Aucune facture récurrente à traiter")

    def process_reminders(self, dry_run=False):
        """
        Traite les rappels de factures qui doivent être envoyés
        """
        self.stdout.write("\nTraitement des rappels...")

        # Trouver les factures qui nécessitent des rappels automatiques
        invoices_needing_reminders = Invoice.objects.filter(
            status__in=["sent", "overdue"]
        )

        reminders_sent = 0

        for invoice in invoices_needing_reminders:
            # Créer les rappels automatiques s'ils n'existent pas
            self.create_automatic_reminders(invoice, dry_run)

            # Traiter les rappels qui doivent être envoyés
            for reminder in invoice.reminders.all():
                if reminder.should_be_sent:
                    self.stdout.write(
                        f"Envoi de rappel {reminder.get_reminder_type_display()} "
                        f"pour {invoice.invoice_number}"
                    )

                    if not dry_run:
                        try:
                            self.send_reminder_email(reminder)
                            reminder.email_sent = True
                            reminder.sent_date = timezone.now()
                            reminder.save()

                            # Mettre à jour le compteur sur la facture
                            invoice.reminder_sent_count += 1
                            invoice.last_reminder_date = timezone.now()
                            invoice.save()

                            reminders_sent += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Rappel envoyé pour {invoice.invoice_number}"
                                )
                            )

                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"✗ Erreur lors de l'envoi du rappel: {e}"
                                )
                            )
                            logger.error(f"Erreur envoi rappel: {e}")
                    else:
                        reminders_sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"[SIMULATION] Rappel envoyé pour {invoice.invoice_number}"
                            )
                        )

        if reminders_sent > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n{reminders_sent} rappel(s) envoyé(s)")
            )
        else:
            self.stdout.write("Aucun rappel à envoyer")

    def create_automatic_reminders(self, invoice, dry_run=False):
        """
        Crée les rappels automatiques pour une facture si ils n'existent pas
        """
        existing_reminders = invoice.reminders.values_list(
            "reminder_type", "days_offset"
        )

        # Rappels par défaut
        default_reminders = [
            ("before_due", -7),  # 7 jours avant
            ("before_due", -3),  # 3 jours avant
            ("on_due_date", 0),  # Le jour même
            ("after_due", 7),  # 7 jours après
            ("after_due", 30),  # 30 jours après
        ]

        for reminder_type, days_offset in default_reminders:
            if (reminder_type, days_offset) not in existing_reminders:
                if not dry_run:
                    InvoiceReminder.objects.create(
                        invoice=invoice,
                        reminder_type=reminder_type,
                        days_offset=days_offset,
                    )

    def send_reminder_email(self, reminder):
        """
        Envoie un email de rappel
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings

        invoice = reminder.invoice
        customer = invoice.customer

        # Préparer le contexte pour le template
        context = {
            "invoice": invoice,
            "customer": customer,
            "reminder": reminder,
            "payment_url": f"{settings.PAYMENT_HOST_URL}/accounts/invoices/{invoice.uuid}/pay/",
        }

        # Choisir le template selon le type de rappel
        if reminder.reminder_type == "before_due":
            if reminder.days_offset == -7:
                subject = (
                    f"Rappel: Facture {invoice.invoice_number} - Échéance dans 7 jours"
                )
            elif reminder.days_offset == -3:
                subject = (
                    f"Rappel: Facture {invoice.invoice_number} - Échéance dans 3 jours"
                )
            else:
                subject = f"Rappel: Facture {invoice.invoice_number} - Échéance proche"

        elif reminder.reminder_type == "on_due_date":
            subject = f"Échéance aujourd'hui: Facture {invoice.invoice_number}"

        elif reminder.reminder_type == "after_due":
            if reminder.days_offset <= 7:
                subject = f"Facture en retard: {invoice.invoice_number}"
            else:
                subject = (
                    f"Facture en retard - Dernière relance: {invoice.invoice_number}"
                )

        # Template email (simplifié)
        message = f"""
Bonjour {customer.get_full_name()},

Nous vous rappelons que la facture {invoice.invoice_number} d'un montant de {invoice.total_amount}€ 
{"est en retard de paiement" if invoice.is_overdue else "arrive à échéance le " + invoice.due_date.strftime('%d/%m/%Y')}.

Vous pouvez payer en ligne en cliquant sur ce lien :
{context['payment_url']}

Cordialement,
L'équipe YEE E-Commerce
"""

        # Envoyer l'email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER or "noreply@yee-commerce.com",
            recipient_list=[customer.email],
            fail_silently=False,
        )
