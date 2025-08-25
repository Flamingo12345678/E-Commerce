# Guide de Configuration Gmail SMTP pour YEE Codes

## ❌ Problème identifié
Erreur 535 : "Username and Password not accepted" lors de l'authentification Gmail SMTP.

## 🔍 Causes possibles
1. **Mot de passe d'application Gmail expiré ou invalide**
2. **Authentification à deux facteurs (2FA) non configurée**
3. **Accès aux applications moins sécurisées désactivé**

## ✅ Solution étape par étape

### Étape 1 : Vérifier l'authentification à deux facteurs
1. Connectez-vous à votre compte Google : https://myaccount.google.com/
2. Allez dans **Sécurité** → **Validation en deux étapes**
3. Assurez-vous que la 2FA est **activée**

### Étape 2 : Générer un nouveau mot de passe d'application
1. Dans **Sécurité** → **Mots de passe des applications**
2. Cliquez sur **Générer un mot de passe d'application**
3. Sélectionnez **Autre (nom personnalisé)**
4. Tapez : "YEE Codes Django SMTP"
5. Copiez le mot de passe généré (16 caractères)

### Étape 3 : Mettre à jour la configuration
Remplacez dans votre fichier `.env` :
```
EMAIL_HOST_PASSWORD=NOUVEAU_MOT_DE_PASSE_APPLICATION
```

### Étape 4 : Activer le SMTP en production
Dans `.env`, remplacez :
```
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Par :
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## 🧪 Test de validation
Après la configuration, exécutez :
```bash
python test_email_config.py
```

## 📧 Configuration actuelle temporaire
- **Mode console activé** : Les emails s'affichent dans la console
- **Configuration SMTP préservée** : Prête pour la production
- **Tous les services fonctionnels** : EmailService opérationnel

## 🚀 Basculement en production
Une fois le mot de passe Gmail mis à jour :
1. Modifiez `EMAIL_BACKEND` dans `.env`
2. Relancez le serveur Django
3. Testez l'envoi d'emails réels

---
*Guide créé le 25 août 2025 pour YEE Codes*
