from django.db import models
from django.core.exceptions import ValidationError
import os


class EmailTemplate(models.Model):
    """Modèle pour gérer les templates d'emails depuis l'interface admin"""

    TEMPLATE_CHOICES = [
        ('welcome', '🎉 Email de bienvenue'),
        ('order_confirmation', '📋 Confirmation de commande'),
        ('order_status_update', '📦 Mise à jour de statut'),
        ('newsletter', '📰 Newsletter'),
    ]

    name = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        unique=True,
        verbose_name="Type de template"
    )
    subject = models.CharField(
        max_length=200,
        verbose_name="Sujet de l'email",
        help_text="Le sujet par défaut pour ce type d'email"
    )
    html_content = models.TextField(
        verbose_name="Contenu HTML",
        help_text="Le contenu HTML du template. Utilisez {{ variable }} pour les variables dynamiques."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Template actif",
        help_text="Désactiver temporairement ce template"
    )
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Template d'email"
        verbose_name_plural = "Templates d'emails"
        ordering = ['name']

    def __str__(self):
        return f"{self.get_name_display()}"

    def get_template_path(self):
        """Retourne le chemin du fichier template"""
        template_files = {
            'welcome': 'emails/welcome.html',
            'order_confirmation': 'emails/order_confirmation.html',
            'order_status_update': 'emails/order_status_update.html',
            'newsletter': 'emails/newsletter.html',
        }
        return template_files.get(self.name, '')

    def save(self, *args, **kwargs):
        """Sauvegarde le template dans le fichier correspondant"""
        super().save(*args, **kwargs)
        self.write_to_file()

    def write_to_file(self):
        """Écrit le contenu du template dans le fichier correspondant"""
        from django.conf import settings
        import os

        template_path = os.path.join(settings.BASE_DIR, 'templates', self.get_template_path())

        try:
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(self.html_content)
        except Exception as e:
            raise ValidationError(f"Erreur lors de l'écriture du template: {e}")

    @classmethod
    def load_from_files(cls):
        """Charge les templates existants depuis les fichiers"""
        from django.conf import settings
        import os

        template_info = {
            'welcome': {
                'subject': '🎉 Bienvenue chez YEE Codes !',
                'path': 'emails/welcome.html'
            },
            'order_confirmation': {
                'subject': '✅ Confirmation de votre commande - YEE Codes',
                'path': 'emails/order_confirmation.html'
            },
            'order_status_update': {
                'subject': '📦 Mise à jour de votre commande - YEE Codes',
                'path': 'emails/order_status_update.html'
            },
            'newsletter': {
                'subject': '📰 Newsletter YEE Codes',
                'path': 'emails/newsletter.html'
            },
        }

        for template_name, info in template_info.items():
            template_path = os.path.join(settings.BASE_DIR, 'templates', info['path'])

            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Créer ou mettre à jour le template en base
                    template_obj, created = cls.objects.get_or_create(
                        name=template_name,
                        defaults={
                            'subject': info['subject'],
                            'html_content': content,
                            'is_active': True
                        }
                    )

                    if not created and template_obj.html_content != content:
                        # Mettre à jour seulement si le contenu a changé
                        template_obj.html_content = content
                        template_obj.save()

                except Exception as e:
                    print(f"Erreur lors du chargement du template {template_name}: {e}")


class EmailTestSend(models.Model):
    """Modèle pour tester l'envoi d'emails depuis l'admin"""

    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        verbose_name="Template à tester"
    )
    test_email = models.EmailField(
        verbose_name="Email de test",
        help_text="L'adresse email où envoyer le test"
    )
    test_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données de test",
        help_text="Variables JSON pour tester le template (ex: {'user_name': 'John', 'order_id': '123'})"
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Test d'email"
        verbose_name_plural = "Tests d'emails"
        ordering = ['-sent_at']

    def __str__(self):
        return f"Test {self.template.name} → {self.test_email}"
