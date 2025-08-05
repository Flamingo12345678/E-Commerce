"""
Services d'email pour les notifications et newsletters
Configuré pour Titan Email avec adresses professionnelles
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from .models import Shopper

logger = logging.getLogger(__name__)


class EmailService:
    """Service centralisé pour l'envoi d'emails avec Titan Email"""

    @staticmethod
    def _get_email_address(email_type):
        """Récupère l'adresse email appropriée selon le type"""
        return settings.EMAIL_ADDRESSES.get(email_type, settings.DEFAULT_FROM_EMAIL)

    @staticmethod
    def send_order_confirmation(shopper, order, items):
        """
        Envoie un email de confirmation de commande
        Utilise: confirmation@y-e-e.tech
        """
        if not shopper.email_notifications:
            logger.info(f"Notifications désactivées pour {shopper.email}")
            return False

        try:
            subject = f"✅ Confirmation de votre commande #{order.id} - YEE Codes"
            from_email = EmailService._get_email_address('order_confirmation')

            # Contenu HTML
            html_content = render_to_string('emails/order_confirmation.html', {
                'shopper': shopper,
                'order': order,
                'items': items,
                'site_name': 'YEE Codes',
                'support_email': 'contact@y-e-e.tech',
                'website_url': 'https://y-e-e.tech'
            })

            # Contenu texte
            text_content = strip_tags(html_content)

            # Création de l'email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[shopper.email],
                reply_to=[settings.REPLY_TO_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            email.send()
            logger.info(f"Email de confirmation envoyé de {from_email} à {shopper.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email confirmation: {e}")
            return False

    @staticmethod
    def send_order_status_update(shopper, order, new_status):
        """
        Envoie un email de mise à jour du statut de commande
        Utilise: confirmation@y-e-e.tech
        """
        if not shopper.email_notifications:
            return False

        try:
            subject = f"📦 Mise à jour de votre commande #{order.id} - YEE Codes"
            from_email = EmailService._get_email_address('order_confirmation')

            html_content = render_to_string('emails/order_status_update.html', {
                'shopper': shopper,
                'order': order,
                'new_status': new_status,
                'site_name': 'YEE Codes',
                'support_email': 'contact@y-e-e.tech',
                'website_url': 'https://y-e-e.tech'
            })

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[shopper.email],
                reply_to=[settings.REPLY_TO_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            email.send()
            logger.info(f"Email de statut envoyé de {from_email} à {shopper.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email statut: {e}")
            return False

    @staticmethod
    def send_newsletter(subject, content, recipients=None):
        """
        Envoie une newsletter aux abonnés
        Utilise: newsletters@y-e-e.tech
        """
        if recipients is None:
            recipients = Shopper.objects.filter(
                newsletter_subscription=True,
                email_notifications=True,
                is_active=True
            )

        sent_count = 0
        error_count = 0
        from_email = EmailService._get_email_address('newsletter')

        for shopper in recipients:
            try:
                full_subject = f"📧 {subject} - Newsletter YEE Codes"

                html_content = render_to_string('emails/newsletter.html', {
                    'shopper': shopper,
                    'content': content,
                    'subject': subject,
                    'site_name': 'YEE Codes',
                    'website_url': 'https://y-e-e.tech',
                    'unsubscribe_url': 'https://y-e-e.tech/accounts/profile/',
                    'support_email': 'contact@y-e-e.tech'
                })

                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject=full_subject,
                    body=text_content,
                    from_email=from_email,
                    to=[shopper.email],
                    reply_to=[settings.REPLY_TO_EMAIL]
                )
                email.attach_alternative(html_content, "text/html")

                email.send()
                sent_count += 1

            except Exception as e:
                logger.error(f"Erreur envoi newsletter à {shopper.email}: {e}")
                error_count += 1

        logger.info(f"Newsletter envoyée de {from_email}: {sent_count} succès, {error_count} erreurs")
        return sent_count, error_count

    @staticmethod
    def send_welcome_email(shopper):
        """
        Envoie un email de bienvenue aux nouveaux utilisateurs
        Utilise: bienvenue@y-e-e.tech
        """
        try:
            subject = "🎉 Bienvenue chez YEE Codes ! Votre compte a été créé avec succès"
            from_email = EmailService._get_email_address('welcome')

            html_content = render_to_string('emails/welcome.html', {
                'shopper': shopper,
                'site_name': 'YEE Codes',
                'website_url': 'https://y-e-e.tech',
                'shop_url': 'https://y-e-e.tech/store/',
                'profile_url': 'https://y-e-e.tech/accounts/profile/',
                'support_email': 'contact@y-e-e.tech'
            })

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[shopper.email],
                reply_to=[settings.REPLY_TO_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            email.send()
            logger.info(f"Email de bienvenue envoyé de {from_email} à {shopper.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email bienvenue: {e}")
            return False

    @staticmethod
    def send_contact_form_notification(name, email, subject, message):
        """
        Envoie une notification pour les formulaires de contact
        Utilise: contact@y-e-e.tech
        """
        try:
            admin_subject = f"📝 Nouveau message de contact - {subject}"
            from_email = EmailService._get_email_address('contact')
            admin_email = EmailService._get_email_address('admin')

            # Email à l'admin
            admin_message = f"""
            Nouveau message de contact reçu sur YEE Codes:
            
            Nom: {name}
            Email: {email}
            Sujet: {subject}
            
            Message:
            {message}
            
            ---
            Envoyé depuis https://y-e-e.tech
            """

            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email=from_email,
                recipient_list=[admin_email],
                fail_silently=False,
            )

            # Email de confirmation à l'utilisateur
            user_subject = "✅ Votre message a été reçu - YEE Codes"
            user_message = f"""
            Bonjour {name},
            
            Nous avons bien reçu votre message concernant "{subject}".
            Notre équipe vous répondra dans les plus brefs délais.
            
            Merci de votre confiance !
            
            L'équipe YEE Codes
            https://y-e-e.tech
            """

            send_mail(
                subject=user_subject,
                message=user_message,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info(f"Notifications de contact envoyées pour {email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi notifications contact: {e}")
            return False
