"""
🔧 GUIDE DE CONFIGURATION TITAN EMAIL POUR YEE CODES
=================================================

## 🚨 ERREUR COURANTE DÉTECTÉE
L'erreur "authentication failed: UGFzc3dvcmQ6" indique un problème d'authentification SMTP.

## ✅ ÉTAPES DE CONFIGURATION TITAN EMAIL

### 1. Vérifier la configuration Titan Email
Dans votre panneau Hostinger/Titan Email :
- ✅ Vérifiez que le compte admin@y-e-e.tech existe
- ✅ Notez le mot de passe EXACT (sensible à la casse)
- ✅ Activez l'accès SMTP si nécessaire

### 2. Configuration .env correcte
```bash
# Configuration SMTP Titan Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.titan.email
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=admin@y-e-e.tech
EMAIL_HOST_PASSWORD=VOTRE_VRAI_MOT_DE_PASSE_TITAN

# ⚠️ IMPORTANT: Remplacez VOTRE_VRAI_MOT_DE_PASSE_TITAN par le vrai mot de passe !
```

### 3. Paramètres SMTP alternatifs à tester
Si le port 587 ne fonctionne pas, essayez :

```bash
# Option 1: Port 465 avec SSL
EMAIL_HOST=smtp.titan.email
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True

# Option 2: Port 25 (parfois bloqué)
EMAIL_HOST=smtp.titan.email
EMAIL_PORT=25
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Option 3: Serveur SMTP alternatif Hostinger
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### 4. Test de connexion SMTP
Pour tester la connexion directement :

```python
# Test dans le shell Django
python manage.py shell

# Dans le shell Python :
from django.core.mail import send_mail
from django.conf import settings

print("Configuration email actuelle:")
print(f"HOST: {settings.EMAIL_HOST}")
print(f"PORT: {settings.EMAIL_PORT}")
print(f"USER: {settings.EMAIL_HOST_USER}")
print(f"TLS: {settings.EMAIL_USE_TLS}")
print(f"SSL: {settings.EMAIL_USE_SSL}")

# Test d'envoi simple
try:
    send_mail(
        'Test SMTP',
        'Message de test depuis Django',
        settings.EMAIL_HOST_USER,
        ['admin@y-e-e.tech'],
        fail_silently=False,
    )
    print("✅ Email envoyé avec succès !")
except Exception as e:
    print(f"❌ Erreur: {e}")
```

### 5. Solutions alternatives si Titan Email pose problème

#### Option A: Gmail (temporaire pour tester)
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-gmail@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-app-gmail
```

#### Option B: SendGrid (professionnel)
```bash
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=votre-clé-api-sendgrid
```

### 6. Vérifications à faire

1. **Vérifier le fichier .env existe** :
   ```bash
   ls -la .env
   ```

2. **Vérifier que Django charge le .env** :
   ```bash
   python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_HOST_USER)"
   ```

3. **Tester la connectivité réseau** :
   ```bash
   telnet smtp.titan.email 587
   ```

### 7. Commande de test corrigée
Une fois la configuration fixée :

```bash
# Test avec utilisateur existant ou création automatique
python manage.py send_newsletter "Test Config Email" "<h1>Test de configuration Titan Email</h1><p>Si vous recevez cet email, la configuration fonctionne !</p>" --test-email admin@y-e-e.tech
```

## 🆘 AIDE SUPPLÉMENTAIRE

Si le problème persiste :

1. **Contactez le support Hostinger** pour vérifier :
   - Que le compte admin@y-e-e.tech est actif
   - Que l'accès SMTP est autorisé
   - Les paramètres SMTP exacts

2. **Vérifiez les logs Hostinger** pour voir les tentatives de connexion

3. **Testez avec un client email classique** (Thunderbird, Mail) d'abord

## 📧 CONFIGURATION FINALE ATTENDUE

Une fois fonctionnel, vous devriez voir :
```
Mode test: envoi uniquement à admin@y-e-e.tech
Envoi de la newsletter à 1 destinataire(s)...
Newsletter envoyée avec succès !
✅ Envoyés: 1
❌ Erreurs: 0
```
"""
