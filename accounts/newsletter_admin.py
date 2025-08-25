"""
Admin personnalisé pour la gestion des newsletters et notifications
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.utils.html import format_html
from accounts.email_services import EmailService
from accounts.models import Shopper


class NewsletterAdmin:
    """Interface d'administration pour les newsletters"""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('newsletter/compose/', self.admin_site.admin_view(self.compose_newsletter), name='compose_newsletter'),
            path('newsletter/subscribers/', self.admin_site.admin_view(self.view_subscribers), name='view_subscribers'),
        ]
        return custom_urls + urls

    def compose_newsletter(self, request):
        """Vue pour composer et envoyer une newsletter"""
        if request.method == 'POST':
            subject = request.POST.get('subject', '').strip()
            content = request.POST.get('content', '').strip()
            send_test = request.POST.get('send_test', False)
            test_email = request.POST.get('test_email', '').strip()

            if not subject or not content:
                messages.error(request, "Le sujet et le contenu sont obligatoires")
                return render(request, 'admin/newsletter_compose.html')

            try:
                if send_test and test_email:
                    # Envoi de test
                    try:
                        test_user = Shopper.objects.get(email=test_email)
                        EmailService.send_newsletter(subject, content, [test_user])
                        messages.success(request, f"Newsletter de test envoyée à {test_email}")
                    except Shopper.DoesNotExist:
                        messages.error(request, f"Utilisateur avec l'email {test_email} non trouvé")
                else:
                    # Envoi réel
                    recipients = Shopper.objects.filter(
                        newsletter_subscription=True,
                        email_notifications=True,
                        is_active=True
                    )

                    sent_count, error_count = EmailService.send_newsletter(subject, content, recipients)

                    messages.success(
                        request,
                        f"Newsletter envoyée ! {sent_count} succès, {error_count} erreurs"
                    )

                    if error_count > 0:
                        messages.warning(request, f"⚠️ {error_count} erreurs lors de l'envoi")

            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi : {str(e)}")

        # Statistiques pour l'affichage
        total_users = Shopper.objects.filter(is_active=True).count()
        newsletter_subscribers = Shopper.objects.filter(
            newsletter_subscription=True,
            email_notifications=True,
            is_active=True
        ).count()

        context = {
            'title': 'Composer une newsletter',
            'total_users': total_users,
            'newsletter_subscribers': newsletter_subscribers,
        }

        return render(request, 'admin/newsletter_compose.html', context)

    def view_subscribers(self, request):
        """Vue pour voir les abonnés à la newsletter"""
        subscribers = Shopper.objects.filter(
            newsletter_subscription=True,
            is_active=True
        ).order_by('-date_joined')

        context = {
            'title': 'Abonnés à la newsletter',
            'subscribers': subscribers,
            'total_count': subscribers.count(),
        }

        return render(request, 'admin/newsletter_subscribers.html', context)


# Ajout des liens dans l'admin principal
def add_newsletter_admin_links(admin_site):
    """Ajoute des liens pour la gestion des newsletters dans l'admin"""

    def newsletter_actions_view(request):
        """Vue principale pour les actions de newsletter"""
        context = {
            'title': 'Gestion des newsletters',
            'available_actions': [
                {
                    'name': 'Composer une newsletter',
                    'url': '/admin/compose_newsletter/',
                    'description': 'Créer et envoyer une newsletter aux abonnés'
                },
                {
                    'name': 'Voir les abonnés',
                    'url': '/admin/view_subscribers/',
                    'description': 'Liste des utilisateurs abonnés à la newsletter'
                },
                {
                    'name': 'Statistiques emails',
                    'url': '/admin/accounts/shopper/',
                    'description': 'Gérer les préférences email des utilisateurs'
                }
            ]
        }
        return render(request, 'admin/newsletter_actions.html', context)

    return newsletter_actions_view
