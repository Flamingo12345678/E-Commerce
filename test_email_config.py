"""
Test de diagnostic pour la configuration email Titan
"""
import os
from django.conf import settings
from django.core.mail import send_mail

print("=== DIAGNOSTIC CONFIGURATION EMAIL ===")
print()

# Test 1: Variables d'environnement
print("1. Variables d'environnement (.env):")
env_vars = [
    'EMAIL_BACKEND',
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_USE_TLS',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD'
]

for var in env_vars:
    value = os.getenv(var, 'NON_DEFINI')
    if 'PASSWORD' in var and value != 'NON_DEFINI':
        print(f"   {var}: {value[:3]}...{value[-3:]}")
    else:
        print(f"   {var}: {value}")

print()

# Test 2: Configuration Django
print("2. Configuration Django (settings.py):")
try:
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'NON_DEFINI')
    if password != 'NON_DEFINI':
        print(f"   EMAIL_HOST_PASSWORD: {password[:3]}...{password[-3:]}")
    else:
        print(f"   EMAIL_HOST_PASSWORD: {password}")
except AttributeError as e:
    print(f"   Erreur: {e}")

print()

# Test 3: Test de connexion SMTP
print("3. Test de connexion SMTP:")
try:
    from django.core.mail import get_connection
    connection = get_connection()
    connection.open()
    print("   ✅ Connexion SMTP réussie")
    connection.close()
except Exception as e:
    print(f"   ❌ Erreur de connexion: {e}")

print()

# Test 4: Test d'envoi simple
print("4. Test d'envoi email simple:")
try:
    send_mail(
        'Test Diagnostic SMTP',
        'Ce message teste la configuration SMTP Titan Email',
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print("   ✅ Email de test envoyé avec succès")
except Exception as e:
    print(f"   ❌ Erreur d'envoi: {e}")

print()
print("=== FIN DU DIAGNOSTIC ===")
