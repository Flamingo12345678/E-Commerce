#!/usr/bin/env python
"""
Test direct de réinitialisation de mot de passe avec Gmail
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def test_password_reset():
    User = get_user_model()

    print("=== TEST RÉINITIALISATION DE MOT DE PASSE ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print()

    # Vérifier les utilisateurs
    users = User.objects.all()
    print(f"Nombre d'utilisateurs: {users.count()}")

    if users.count() == 0:
        print("Aucun utilisateur trouvé. Création d'un utilisateur test...")
        user = User.objects.create_user(
            username='testuser',
            email='ernestyombi20@gmail.com',
            password='temppassword123'
        )
        print(f"Utilisateur créé: {user.username}")
    else:
        # Prendre le premier utilisateur ou celui avec votre email
        try:
            user = User.objects.get(email='ernestyombi20@gmail.com')
        except User.DoesNotExist:
            user = users.first()
            user.email = 'ernestyombi20@gmail.com'
            user.save()
        print(f"Utilisateur utilisé: {user.username} ({user.email})")

    # Générer le token de réinitialisation
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # URL de réinitialisation
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    reset_url = f"{site_url}/accounts/password-reset-confirm/{uid}/{token}/"

    print(f"URL générée: {reset_url}")

    # Préparer l'email
    subject = "🔑 Test Réinitialisation YEE Codes - Gmail"

    text_content = f"""
Bonjour {user.username},

Ceci est un test de réinitialisation de mot de passe via Gmail.

Cliquez sur le lien suivant pour réinitialiser votre mot de passe:
{reset_url}

Ce lien est valide pendant 3 jours.

L'équipe YEE Codes
"""

    try:
        # Contenu HTML si le template existe
        html_content = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'YEE Codes',
            'site_url': site_url,
            'support_email': 'ernestyombi20@gmail.com',
        })
        print("Template HTML trouvé et rendu avec succès")
    except Exception as e:
        print(f"Template HTML non trouvé, utilisation du texte seul: {e}")
        html_content = f"<pre>{text_content}</pre>"

    # Envoyer l'email
    try:
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[getattr(settings, 'REPLY_TO_EMAIL', settings.DEFAULT_FROM_EMAIL)]
        )
        email_message.attach_alternative(html_content, "text/html")

        result = email_message.send()

        if result == 1:
            print("✅ EMAIL ENVOYÉ AVEC SUCCÈS VIA GMAIL!")
            print(f"📧 Vérifiez votre boîte de réception Gmail: {user.email}")
            print(f"📋 Sujet: {subject}")
            print(f"🔗 Lien de réinitialisation: {reset_url}")
        else:
            print(f"❌ Échec d'envoi. Résultat: {result}")

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        print("L'email sera probablement affiché dans la console (mode développement)")

    print("\n=== FIN DU TEST ===")

if __name__ == "__main__":
    test_password_reset()
