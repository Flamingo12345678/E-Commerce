"""
Test de diagnostic complet pour la configuration email YEE Codes
Version améliorée avec tests détaillés
"""
import os
import django
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail, get_connection
from accounts.email_services import EmailService

print("=== DIAGNOSTIC COMPLET CONFIGURATION EMAIL YEE CODES ===")
print()

# Test 1: Variables d'environnement
print("1. Variables d'environnement (.env):")
env_vars = [
    'EMAIL_BACKEND',
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_USE_TLS',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'SITE_DOMAIN',
    'SITE_URL'
]

for var in env_vars:
    value = os.getenv(var, 'NON_DEFINI')
    if 'PASSWORD' in var and value != 'NON_DEFINI':
        print(f"   ✅ {var}: {value[:3]}...{value[-3:]}")
    else:
        print(f"   ✅ {var}: {value}")

print()

# Test 2: Configuration Django settings
print("2. Configuration Django (settings.py):")
try:
    print(f"   ✅ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   ✅ EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   ✅ EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   ✅ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   ✅ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   ✅ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   ✅ SITE_DOMAIN: {getattr(settings, 'SITE_DOMAIN', 'Non défini')}")
    print(f"   ✅ SITE_URL: {getattr(settings, 'SITE_URL', 'Non défini')}")

    password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'NON_DEFINI')
    if password != 'NON_DEFINI':
        print(f"   ✅ EMAIL_HOST_PASSWORD: {password[:3]}...{password[-3:]}")
    else:
        print(f"   ❌ EMAIL_HOST_PASSWORD: {password}")

except AttributeError as e:
    print(f"   ❌ Erreur: {e}")

print()

# Test 3: Configuration des adresses email spécialisées
print("3. Adresses email spécialisées:")
try:
    email_addresses = settings.EMAIL_ADDRESSES
    for email_type, address in email_addresses.items():
        print(f"   ✅ {email_type}: {address}")
except AttributeError:
    print("   ❌ EMAIL_ADDRESSES non configuré")

print()

# Test 4: Test de connexion SMTP
print("4. Test de connexion SMTP:")
try:
    if 'console' in settings.EMAIL_BACKEND:
        print("   ⚠️  Backend console activé - pas de test SMTP réel")
    else:
        connection = get_connection()
        connection.open()
        print("   ✅ Connexion SMTP réussie")
        connection.close()
except Exception as e:
    print(f"   ❌ Erreur de connexion SMTP: {e}")

print()

# Test 5: Test d'envoi email simple
print("5. Test d'envoi email simple:")
try:
    if 'console' in settings.EMAIL_BACKEND:
        print("   ⚠️  Mode console - l'email s'affichera dans la console")

    result = send_mail(
        'Test Configuration Email YEE Codes',
        'Ce message teste la configuration email unifiée.',
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )

    if result:
        print("   ✅ Email de test envoyé avec succès")
    else:
        print("   ❌ Échec de l'envoi de l'email de test")

except Exception as e:
    print(f"   ❌ Erreur d'envoi: {e}")

print()

# Test 6: Test du service EmailService
print("6. Test du service EmailService:")
try:
    # Test de la méthode de test intégrée
    result = EmailService.test_email_configuration()
    if result:
        print("   ✅ Service EmailService fonctionnel")
    else:
        print("   ❌ Service EmailService défaillant")

    # Test des méthodes helper
    site_info = EmailService._get_site_info()
    print(f"   ✅ Site info: {site_info}")

    welcome_email = EmailService._get_email_address('welcome')
    print(f"   ✅ Email bienvenue: {welcome_email}")

except Exception as e:
    print(f"   ❌ Erreur service EmailService: {e}")

print()

# Test 7: Vérification des templates
print("7. Vérification des templates email:")
template_files = [
    'emails/welcome.html',
    'emails/order_confirmation.html',
    'emails/order_status_update.html',
    'emails/newsletter.html'
]

templates_dir = Path(settings.BASE_DIR) / 'templates'
for template in template_files:
    template_path = templates_dir / template
    if template_path.exists():
        print(f"   ✅ {template}: Trouvé")
    else:
        print(f"   ❌ {template}: Manquant")

print()

# Résumé de la configuration
print("=== RÉSUMÉ DE LA CONFIGURATION ===")
print(f"Backend email: {settings.EMAIL_BACKEND}")
print(f"Serveur SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"TLS activé: {settings.EMAIL_USE_TLS}")
print(f"Utilisateur: {settings.EMAIL_HOST_USER}")
print(f"Domaine principal: {getattr(settings, 'SITE_DOMAIN', 'Non défini')}")
print(f"URL du site: {getattr(settings, 'SITE_URL', 'Non défini')}")

print()
print("=== RECOMMANDATIONS ===")

# Vérifications et recommandations
if 'console' in settings.EMAIL_BACKEND:
    print("⚠️  Mode développement: Backend console activé")
    print("   Pour la production, activez le backend SMTP dans .env")

if not settings.EMAIL_HOST_PASSWORD:
    print("❌ Mot de passe email manquant")
    print("   Configurez EMAIL_HOST_PASSWORD dans .env")

if getattr(settings, 'SITE_DOMAIN', None) == 'y-e-e.tech':
    print("✅ Domaine principal configuré correctement")
else:
    print("⚠️  Vérifiez la configuration du domaine principal")

print()
print("=== FIN DU DIAGNOSTIC ===")
