# Guide de déploiement Azure pour votre application Django E-Commerce

## Variables d'environnement à configurer dans Azure App Service

Dans le portail Azure, allez dans votre App Service > Configuration > Application settings et ajoutez :

### Variables Django essentielles :
- SECRET_KEY = "votre-clé-secrète-django"
- DEBUG = "False"
- ALLOWED_HOSTS = "flam-ecommerce-1754047481.azurewebsites.net,*.azurewebsites.net"

### Base de données MySQL Azure :
- DB_NAME = "nom-de-votre-base"
- DB_USER = "utilisateur-mysql"
- DB_PASSWORD = "mot-de-passe-mysql"
- DB_HOST = "serveur-mysql.mysql.database.azure.com"
- DB_PORT = "3306"

### Configuration des paiements :
- STRIPE_PUBLISHABLE_KEY = "pk_live_votre_clé"
- STRIPE_SECRET_KEY = "sk_live_votre_clé"
- STRIPE_WEBHOOK_SECRET = "whsec_votre_secret"
- PAYPAL_CLIENT_ID = "votre_client_id"
- PAYPAL_CLIENT_SECRET = "votre_secret"
- PAYMENT_HOST_URL = "https://flam-ecommerce-1754047481.azurewebsites.net"

### Configuration Firebase :
- FIREBASE_API_KEY = "votre-api-key"
- FIREBASE_AUTH_DOMAIN = "votre-projet.firebaseapp.com"
- FIREBASE_PROJECT_ID = "votre-projet-id"
- FIREBASE_STORAGE_BUCKET = "votre-projet.appspot.com"
- FIREBASE_MESSAGING_SENDER_ID = "votre-sender-id"
- FIREBASE_APP_ID = "votre-app-id"

## Commandes Azure CLI pour déployer

1. Créer une base de données MySQL Flexible Server (nouvelle version recommandée) :
```bash
# Créer le serveur MySQL Flexible
az mysql flexible-server create \
  --resource-group E-Commerce \
  --name flam-server \
  --location "France Central" \
  --admin-user Flamingo \
  --admin-password 'Fl@mingo_237*' \
  --sku-name Standard_B2s \
  --tier Burstable \
  --public-access 0.0.0.0 \
  --storage-size 32 \
  --version 8.0.21

# Créer la base de données
az mysql flexible-server db create \
  --resource-group E-Commerce \
  --server-name flam-server \
  --database-name ecommerce_db

# Configurer les règles de pare-feu pour permettre les connexions Azure
az mysql flexible-server firewall-rule create \
  --resource-group E-Commerce \
  --name flam-server \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

2. Créer l'App Service Plan et l'App Service :
```bash
# Le plan App Service existe déjà
# L'App Service a été créée avec le nom : flam-ecommerce-1754047481
```

3. Configurer l'App Service :
```bash
# Configurer le fichier de démarrage
az webapp config set \
  --resource-group E-Commerce \
  --name flam-ecommerce-1754047481 \
  --startup-file startup.sh

# Configurer les variables d'environnement essentielles
az webapp config appsettings set \
  --resource-group E-Commerce \
  --name flam-ecommerce-1754047481 \
  --settings \
    DEBUG=False \
    DB_HOST=flam-server.mysql.database.azure.com \
    DB_NAME=ecommerce_db \
    DB_USER=Flamingo \
    DB_PASSWORD='Fl@mingo_237*' \
    DB_PORT=3306
```

## Checklist avant déploiement :
- [x] App Service créée (flam-ecommerce-1754047481)
- [ ] Variables d'environnement configurées dans Azure
- [ ] Base de données MySQL créée et accessible
- [ ] Secrets GitHub configurés
- [ ] Fichier firebase-credentials.json uploadé
- [ ] DNS configuré si domaine personnalisé

## Post-déploiement :
1. Vérifier les logs : `az webapp log tail --name flam-ecommerce-1754047481 --resource-group E-Commerce`
2. Exécuter les migrations : Se connecter via SSH et exécuter `python manage.py migrate`
3. Créer un superutilisateur : `python manage.py createsuperuser`
