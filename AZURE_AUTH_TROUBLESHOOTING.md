# Guide de résolution de l'erreur d'authentification Azure

## 🚨 Erreur rencontrée
```
Error: Login failed with Error: Using auth-type: SERVICE_PRINCIPAL. 
Not all values are present. Ensure 'client-id' and 'tenant-id' are supplied.
```

## 🔍 Causes possibles
1. **Secrets GitHub manquants ou mal configurés**
2. **Service Principal Azure non créé**
3. **Permissions insuffisantes**
4. **Format de credentials incorrect**

## ✅ Solutions étape par étape

### 1. Créer un Service Principal Azure
```bash
# Se connecter à Azure CLI
az login

# Obtenir votre Subscription ID
az account show --query id --output tsv

# Créer le service principal (remplacez SUBSCRIPTION_ID)
az ad sp create-for-rbac \
  --name "github-actions-ecommerce" \
  --role contributor \
  --scopes /subscriptions/VOTRE_SUBSCRIPTION_ID/resourceGroups/E-Commerce \
  --sdk-auth
```

### 2. Configurer les secrets GitHub
Dans votre repository GitHub : **Settings > Secrets and variables > Actions**

#### Option A : Secret unique (recommandé)
- **Nom** : `AZURE_CREDENTIALS`
- **Valeur** : JSON complet de l'étape 1

#### Option B : Secrets individuels
- `AZURE_CLIENT_ID` : clientId du JSON
- `AZURE_TENANT_ID` : tenantId du JSON  
- `AZURE_SUBSCRIPTION_ID` : subscriptionId du JSON
- `AZURE_CLIENT_SECRET` : clientSecret du JSON

### 3. Vérifier la configuration Azure App Service
```bash
# Vérifier que l'App Service existe
az webapp show --name flam-ecommerce-1754047481 --resource-group E-Commerce

# Vérifier les permissions du service principal
az role assignment list --assignee CLIENT_ID --scope /subscriptions/SUBSCRIPTION_ID/resourceGroups/E-Commerce
```

## 🧪 Test de validation
```bash
# Tester l'authentification localement
az login --service-principal \
  --username CLIENT_ID \
  --password CLIENT_SECRET \
  --tenant TENANT_ID

# Si succès, tester le déploiement
az webapp deployment source config-zip \
  --resource-group E-Commerce \
  --name flam-ecommerce-1754047481 \
  --src app.zip
```

## 🔧 Configuration alternative pour Azure CLI local
Si vous déployez localement, créez un fichier `.azure/credentials` :
```json
{
  "subscriptionId": "votre-subscription-id",
  "tenantId": "votre-tenant-id",
  "clientId": "votre-client-id",
  "clientSecret": "votre-client-secret"
}
```

## 📝 Variables d'environnement requises pour l'App Service
Dans le portail Azure, configurez ces variables :

### Essentielles
- `SECRET_KEY` : Clé secrète Django
- `DEBUG` : False
- `ALLOWED_HOSTS` : flam-ecommerce-1754047481.azurewebsites.net,*.azurewebsites.net

### Base de données
- `DB_NAME` : Nom de votre base MySQL
- `DB_USER` : Utilisateur MySQL  
- `DB_PASSWORD` : Mot de passe MySQL
- `DB_HOST` : Serveur MySQL Azure
- `DB_PORT` : 3306

### Paiements
- `STRIPE_PUBLISHABLE_KEY` : pk_live_...
- `STRIPE_SECRET_KEY` : sk_live_...
- `PAYPAL_CLIENT_ID` : Votre client ID PayPal

## 🚀 Commandes de déploiement rapide
```bash
# 1. Construire l'application
pip install -r requirements.txt
python manage.py collectstatic --noinput

# 2. Créer le package de déploiement
zip -r app.zip . -x "*.git*" "*__pycache__*" "*.pyc" "venv/*"

# 3. Déployer sur Azure
az webapp deployment source config-zip \
  --resource-group E-Commerce \
  --name flam-ecommerce-1754047481 \
  --src app.zip

# 4. Exécuter les migrations
az webapp ssh --resource-group E-Commerce --name flam-ecommerce-1754047481
# Dans le terminal SSH : python manage.py migrate
```

## 🔒 Sécurité
- ❌ Ne jamais commiter les secrets dans le code
- ✅ Utiliser Azure Key Vault pour la production
- ✅ Rotation régulière des secrets
- ✅ Principle of least privilege pour les permissions
