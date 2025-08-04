# 🚀 Guide de Déploiement App Platform Digital Ocean

## Configuration Automatisée via GitHub

Votre application est maintenant configurée pour se déployer automatiquement sur l'App Platform de Digital Ocean directement depuis votre repository GitHub avec le domaine **y-e-e.codes**.

## 📋 Étapes de Déploiement

### 1. Finaliser la Configuration GitHub

```bash
# Ajouter et pousser les derniers changements
git add .
git commit -m "Configuration App Platform Digital Ocean pour y-e-e.codes"
git push origin main
```

### 2. Créer l'Application sur Digital Ocean

1. **Connectez-vous** à Digital Ocean
2. Allez dans **App Platform**
3. Cliquez sur **"Create App"**
4. Sélectionnez **GitHub** comme source
5. Choisissez votre repository **YEE E-Commerce**
6. Sélectionnez la branche **main**
7. **Utilisez le fichier app.yaml** détecté automatiquement dans `.do/app.yaml`

### 3. Configuration DNS pour y-e-e.codes

**Important :** Avant de déployer, vérifiez que vos DNS chez Name.com pointent correctement :

#### Enregistrements DNS requis chez Name.com :
```
Type    Nom             Valeur                          TTL
A       @               [IP fournie par DigitalOcean]   300
CNAME   www             y-e-e.codes                     300
```

**Note :** L'IP sera fournie par DigitalOcean après la création de l'app.

### 4. Configuration des Variables d'Environnement

L'App Platform va automatiquement détecter le fichier `.do/app.yaml` qui contient toute la configuration. Vous devrez configurer les valeurs secrètes dans l'interface Digital Ocean :

#### Variables Obligatoires à Configurer dans l'interface DO :
- `SECRET_KEY` : Générez une clé secrète Django sécurisée
- `STRIPE_PUBLISHABLE_KEY` : Votre clé publique Stripe
- `STRIPE_SECRET_KEY` : Votre clé secrète Stripe
- `STRIPE_WEBHOOK_SECRET` : Secret pour les webhooks Stripe
- `PAYPAL_CLIENT_ID` : ID client PayPal
- `PAYPAL_CLIENT_SECRET` : Secret client PayPal
- `EMAIL_HOST_USER` : Votre email pour l'envoi
- `EMAIL_HOST_PASSWORD` : Mot de passe d'application email
- `FIREBASE_CREDENTIALS` : Contenu du fichier firebase-credentials.json (en JSON)

### 5. Base de Données PostgreSQL

L'App Platform va automatiquement :
- ✅ Créer une base PostgreSQL
- ✅ Configurer la variable `DATABASE_URL`
- ✅ Connecter votre application à la base

### 6. Configuration du Domaine y-e-e.codes

1. Dans les paramètres de l'app, allez dans **"Domains"**
2. Le domaine **y-e-e.codes** et **www.y-e-e.codes** sont déjà pré-configurés dans app.yaml
3. Suivez les instructions pour configurer les DNS chez Name.com
4. SSL sera automatiquement configuré par Let's Encrypt

## 🔧 Configuration Post-Déploiement

### 1. Exécuter les Migrations

Une fois l'app déployée, vous devrez exécuter les migrations Django :

1. Allez dans **App Platform** > **Votre App** > **Console**
2. Ou connectez-vous via SSH si activé
3. Exécutez :

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 2. Tester l'Application

Votre application sera accessible sur :
- URL temporaire : `https://yee-ecommerce-xxxxx.ondigitalocean.app`
- Domaine personnalisé : `https://y-e-e.codes` (après configuration DNS)
- Alias www : `https://www.y-e-e.codes`

### 3. Configuration des Webhooks

Configurez les URLs de webhook dans vos comptes avec votre domaine y-e-e.codes :

**Stripe :**
- URL : `https://y-e-e.codes/accounts/stripe/webhook/`

**PayPal :**
- URL : `https://y-e-e.codes/accounts/paypal/webhook/`

## 📊 Surveillance et Maintenance

### Logs de l'Application
- Accès direct via l'interface Digital Ocean App Platform
- Section **"Runtime Logs"** pour voir les logs en temps réel

### Métriques
- CPU, RAM, et trafic réseau visibles dans l'interface
- Alertes automatiques configurables

### Mises à Jour Automatiques
- Chaque push sur la branche `main` déclenche un redéploiement
- Rollback automatique en cas d'erreur

## 🔒 Sécurité

### Variables d'Environnement Sécurisées
- Toutes les clés sensibles sont stockées de manière chiffrée
- Accès restreint aux variables d'environnement

### HTTPS
- SSL/TLS automatiquement configuré
- Redirection HTTP vers HTTPS

### Base de Données
- PostgreSQL managée avec sauvegardes automatiques
- Chiffrement au repos et en transit

## 💰 Coûts Estimés

**Configuration Recommandée :**
- **Basic Plan** : ~25$/mois
  - 1 vCPU, 512 MB RAM
  - PostgreSQL Basic
  - 100 GB de bande passante

**Évolution :**
- Scale automatiquement selon le trafic
- Passage en **Professional** si nécessaire

## 🚨 Dépannage

### Problèmes Courants

**1. Erreurs de Build :**
- Vérifiez les logs de build dans l'interface
- Assurez-vous que `requirements.txt` est complet

**2. Erreurs de Base de Données :**
- Vérifiez que les migrations ont été exécutées
- Consultez les logs runtime

**3. Fichiers Statiques :**
- Automatiquement gérés par `collectstatic` dans le build
- Servis directement par l'App Platform

### Commandes Utiles

```bash
# Voir les logs en temps réel
doctl apps logs <app-id> --follow

# Redéployer manuellement
doctl apps create-deployment <app-id>

# Lister les apps
doctl apps list
```

## 🎯 Prochaines Étapes

1. **Déployez** en suivant ce guide
2. **Testez** toutes les fonctionnalités
3. **Configurez** le domaine personnalisé
4. **Passez en production** (clés Stripe/PayPal live)
5. **Surveillez** les performances

L'App Platform de Digital Ocean simplifie énormément le déploiement et la maintenance. Votre application sera automatiquement mise à jour à chaque push sur GitHub !
