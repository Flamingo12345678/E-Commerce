#!/usr/bin/env python
"""
Script pour corriger les redirections OAuth2 - YEE Codes
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings

def fix_oauth_redirections():
    print("=== CORRECTION DES REDIRECTIONS OAUTH2 ===")
    print()

    # 1. Mettre à jour le site par défaut
    site = Site.objects.get(pk=1)
    print(f"Site actuel: {site.domain}")

    # Utiliser localhost pour le développement
    old_domain = site.domain
    site.domain = 'localhost:8000'
    site.name = 'YEE Codes - Développement'
    site.save()

    print(f"✅ Site mis à jour: {old_domain} → {site.domain}")
    print()

    # 2. Vérifier et afficher les URLs de redirection correctes
    print("📋 URLs de redirection OAuth2 à configurer dans vos consoles :")
    print()
    print("🔵 GOOGLE OAuth2 Console (https://console.cloud.google.com/):")
    print(f"   URI de redirection autorisée: http://localhost:8000/accounts/google/login/callback/")
    print()
    print("🔴 FACEBOOK Developers (https://developers.facebook.com/):")
    print(f"   URI de redirection OAuth valide: http://localhost:8000/accounts/facebook/login/callback/")
    print()

    # 3. Vérifier les applications sociales
    print("📱 Applications sociales configurées :")
    social_apps = SocialApp.objects.all()

    for app in social_apps:
        print(f"   {app.provider.title()}: {app.name}")
        print(f"   Client ID: {app.client_id[:20]}...")

        # Vérifier que l'app est associée au bon site
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)
            print(f"   ✅ Site {site.domain} ajouté à l'application")
        else:
            print(f"   ✅ Site {site.domain} déjà associé")
        print()

    # 4. Vérifier la configuration Django
    print("⚙️  Configuration Django :")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"   SITE_ID: {settings.SITE_ID}")
    print(f"   DEBUG: {settings.DEBUG}")
    print()

    # 5. Instructions pour les URLs de production
    print("🚀 Pour la production, mettez à jour :")
    print("   1. Le domaine du site vers 'y-e-e.tech'")
    print("   2. Les URLs de redirection OAuth vers 'https://y-e-e.tech/accounts/.../login/callback/'")
    print()

    print("✅ Configuration des redirections OAuth2 terminée !")
    print()
    print("🧪 Test maintenant :")
    print("   1. Allez sur http://localhost:8000/accounts/login/")
    print("   2. Cliquez sur 'Continuer avec Google' ou 'Continuer avec Facebook'")
    print("   3. Les redirections devraient maintenant fonctionner correctement")

if __name__ == "__main__":
    fix_oauth_redirections()
