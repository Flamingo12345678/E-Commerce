#!/usr/bin/env python
"""
Script pour configurer les applications sociales Django Allauth
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings

def configure_social_apps():
    print("=== CONFIGURATION DES APPLICATIONS SOCIALES ===")

    # Obtenir le site actuel
    site = Site.objects.get_current()
    print(f"Site actuel: {site.domain}")

    # Vérifier les applications existantes
    existing_apps = SocialApp.objects.all()
    print(f"Applications sociales existantes: {existing_apps.count()}")

    for app in existing_apps:
        print(f"  - {app.provider}: {app.name}")

    print()

    # Configurer Google OAuth2
    try:
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth2',
                'client_id': settings.SOCIALACCOUNT_GOOGLE_OAUTH2_CLIENT_ID,
                'secret': settings.SOCIALACCOUNT_GOOGLE_OAUTH2_CLIENT_SECRET,
            }
        )

        if not google_app.sites.filter(id=site.id).exists():
            google_app.sites.add(site)

        if created:
            print("✅ Application Google OAuth2 créée")
        else:
            # Mettre à jour les clés si nécessaire
            google_app.client_id = settings.SOCIALACCOUNT_GOOGLE_OAUTH2_CLIENT_ID
            google_app.secret = settings.SOCIALACCOUNT_GOOGLE_OAUTH2_CLIENT_SECRET
            google_app.save()
            print("✅ Application Google OAuth2 mise à jour")

    except Exception as e:
        print(f"❌ Erreur Google OAuth2: {e}")

    # Configurer Facebook OAuth2
    try:
        facebook_app, created = SocialApp.objects.get_or_create(
            provider='facebook',
            defaults={
                'name': 'Facebook OAuth2',
                'client_id': settings.SOCIALACCOUNT_FACEBOOK_APP_ID,
                'secret': settings.SOCIALACCOUNT_FACEBOOK_APP_SECRET,
            }
        )

        if not facebook_app.sites.filter(id=site.id).exists():
            facebook_app.sites.add(site)

        if created:
            print("✅ Application Facebook OAuth2 créée")
        else:
            # Mettre à jour les clés si nécessaire
            facebook_app.client_id = settings.SOCIALACCOUNT_FACEBOOK_APP_ID
            facebook_app.secret = settings.SOCIALACCOUNT_FACEBOOK_APP_SECRET
            facebook_app.save()
            print("✅ Application Facebook OAuth2 mise à jour")

    except Exception as e:
        print(f"❌ Erreur Facebook OAuth2: {e}")

    print()

    # Vérifier la configuration finale
    print("=== CONFIGURATION FINALE ===")
    social_apps = SocialApp.objects.all()
    for app in social_apps:
        sites_count = app.sites.count()
        print(f"📱 {app.provider.title()}: {app.name}")
        print(f"   Client ID: {app.client_id[:15]}...")
        print(f"   Sites associés: {sites_count}")
        print()

    print("🎉 Configuration des applications sociales terminée!")
    print()
    print("Maintenant, vous pouvez tester vos boutons de connexion sociale :")
    print("- Page de connexion: http://localhost:8000/accounts/login/")
    print("- Page d'inscription: http://localhost:8000/accounts/signup/")

if __name__ == "__main__":
    configure_social_apps()
