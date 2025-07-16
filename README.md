# 🛒 E-Commerce Platform Django

Plateforme e-commerce complète développée avec Django, intégrant un système de paiement avancé avec Stripe et PayPal, authentification à double facteur, et système de facturation natif.

## 🚀 Fonctionnalités Principales

### 💳 Système de Paiement Complet
- **Intégration Stripe** : Cartes de crédit, paiements sécurisés, webhooks
- **Intégration PayPal** : Paiements PayPal, abonnements
- **Gestion des méthodes de paiement** : Sauvegarde sécurisée, cartes par défaut
- **Webhooks temps réel** : Synchronisation automatique des paiements
- **Facturation native** : Génération et gestion des factures

### 🔐 Sécurité Avancée
- **Authentification 2FA** : TOTP avec Google Authenticator
- **Protection CSRF** : Sécurisation des formulaires
- **Validation des webhooks** : Signatures cryptographiques
- **Gestion des sessions** : Expiration automatique

### 📦 Gestion E-Commerce
- **Catalogue produits** : Articles, catégories, images
- **Panier d'achat** : Gestion quantités, totaux
- **Gestion stock** : Suivi inventaire en temps réel
- **Commandes** : Workflow complet de la commande à la livraison

### 🏪 Interface Administration
- **Dashboard admin** : Vue d'ensemble des ventes
- **Gestion produits** : CRUD complet avec upload d'images
- **Suivi commandes** : États, historique, notifications
- **Analytiques** : Rapports de vente, statistiques

## 🛠️ Technologies Utilisées

### Backend
- **Django 5.2.4** - Framework web Python
- **SQLite** - Base de données (développement)
- **Pillow** - Traitement d'images
- **django-environ** - Gestion variables d'environnement

### Paiements & Facturation
- **Stripe 11.6.0** - Processeur de paiement principal
- **PayPal REST SDK** - Intégration PayPal
- **Facturation native** - Système interne de factures

### Sécurité & Authentification
- **django-two-factor-auth** - Authentification 2FA
- **django-otp** - Codes à usage unique
- **pyotp** - Génération TOTP
- **qrcode** - QR codes pour configuration 2FA

### Interface Utilisateur
- **django-crispy-forms** - Formulaires stylisés
- **django-formtools** - Formulaires multi-étapes
- **Templates Bootstrap** - Interface responsive

## 📦 Installation

### Prérequis
- Python 3.11+
- pip
- virtualenv (recommandé)

### Configuration

1. **Cloner le projet**
```bash
git clone <votre-repo>
cd E-Commerce
```

2. **Créer un environnement virtuel**
```bash
python -m venv env
source env/bin/activate  # macOS/Linux
# ou
env\Scripts\activate     # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration des variables d'environnement**
```bash
cp .env.example .env
```

Éditer `.env` avec vos clés :
```env
# Django
SECRET_KEY=votre-cle-secrete-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_ENDPOINT_SECRET=whsec_...

# PayPal
PAYPAL_CLIENT_ID=votre-client-id
PAYPAL_CLIENT_SECRET=votre-secret
PAYPAL_MODE=sandbox  # ou 'live' pour production
```

5. **Migrations et setup initial**
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

6. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

L'application sera accessible sur `http://127.0.0.1:8000/`

## 🔧 Configuration Avancée

### Configuration Stripe

1. **Créer un compte Stripe** sur [stripe.com](https://stripe.com)
2. **Récupérer les clés API** dans le dashboard Stripe
3. **Configurer les webhooks** :
   - URL : `https://votre-domaine.com/accounts/webhook/stripe/`
   - Événements : `payment_intent.succeeded`, `payment_method.attached`

### Configuration PayPal

1. **Créer une application PayPal** sur [developer.paypal.com](https://developer.paypal.com)
2. **Récupérer Client ID et Secret**
3. **Configurer les URLs de retour** dans votre application PayPal

### Configuration 2FA

L'authentification à double facteur est automatiquement disponible :
- Accès via `/account/login/`
- Configuration QR code dans le profil utilisateur
- Support Google Authenticator, Authy, etc.

## 🧪 Tests

### Lancer les tests
```bash
# Tests complets
python manage.py test

# Tests spécifiques
python manage.py test accounts.tests
python manage.py test store.tests

# Tests de paiement
python test_payment_system.py
python test_webhooks.py
```

### Tests d'intégration paiement
```bash
# Test Stripe
python test_integration_payment.py

# Test méthodes de paiement
python test_payment_methods.py
```

## 📊 Monitoring & Logs

### Logs disponibles
- `django.log` - Logs généraux de l'application
- `payment.log` - Logs spécifiques aux paiements
- `webhook_debug.log` - Debug des webhooks

### Commandes utiles
```bash
# Vérifier les logs en temps réel
tail -f django.log
tail -f payment.log

# Debug webhooks
python debug_webhooks.py
```

## 🚀 Déploiement

### Variables d'environnement production
```env
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com
SECRET_KEY=cle-secrete-forte

# URLs de production
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
PAYPAL_MODE=live
```

### Checklist déploiement
- [ ] Variables d'environnement configurées
- [ ] Base de données migrée
- [ ] Fichiers statiques collectés
- [ ] HTTPS configuré
- [ ] Webhooks configurés avec les bonnes URLs
- [ ] Backups automatiques configurés

## 📚 Documentation Technique

### Guides disponibles
- `SYSTEME_FACTURATION_GUIDE.md` - Système de facturation complet
- `GUIDE_TEST_PAIEMENTS.md` - Tests et validation des paiements
- `MISSION_2FA_ACCOMPLIE.md` - Implémentation 2FA
- `RAPPORT_FINAL_IMPLEMENTATION_PAIEMENT.md` - Rapport technique paiements

### Architecture
```
E-Commerce/
├── accounts/          # Gestion utilisateurs, paiements, facturation
├── store/            # Catalogue, panier, commandes
├── shop/             # Configuration Django principale
├── templates/        # Templates HTML
├── static/          # Fichiers CSS, JS, images
├── media/           # Uploads utilisateurs
└── requirements.txt # Dépendances Python
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

### Issues communes

**Erreur de webhook Stripe**
```bash
# Vérifier la signature
python test_stripe_signature.py
```

**Problème de paiement PayPal**
```bash
# Debug PayPal
python debug_webhook_headers.py
```

**Erreur 2FA**
- Vérifier la synchronisation de l'horloge
- Regénérer le QR code si nécessaire

### Contact
- 📧 Email : [votre-email]
- 🐛 Issues : [lien-vers-issues]
- 📖 Wiki : [lien-vers-wiki]

---

**🎉 Plateforme e-commerce prête pour la production !**

✅ Paiements sécurisés | ✅ 2FA activé | ✅ Facturation native | ✅ Interface admin complète
# E-Commerce
