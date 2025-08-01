#!/bin/bash

# Script pour obtenir vos informations Azure réelles
# Ce script vous aidera à résoudre l'erreur "Subscription not found"

echo "🔍 Récupération de vos informations Azure"
echo "========================================"

# Vérifier si Azure CLI est installé
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI n'est pas installé."
    echo "📥 Installation via Homebrew: brew install azure-cli"
    exit 1
fi

echo "✅ Azure CLI détecté"
echo ""

# Vérifier si l'utilisateur est connecté
echo "🔐 Vérification de la connexion Azure..."
if ! az account show &> /dev/null; then
    echo "❌ Vous n'êtes pas connecté à Azure"
    echo "🔑 Connectez-vous avec: az login"
    echo "   Cela ouvrira votre navigateur pour l'authentification"
    exit 1
fi

echo "✅ Connecté à Azure"
echo ""

# Obtenir les informations du compte actuel
echo "📋 Vos informations Azure actuelles:"
echo "======================================"

# Subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
echo "🆔 Subscription ID: $SUBSCRIPTION_ID"

# Tenant ID
TENANT_ID=$(az account show --query tenantId --output tsv)
echo "🏢 Tenant ID: $TENANT_ID"

# Nom de la subscription
SUBSCRIPTION_NAME=$(az account show --query name --output tsv)
echo "📝 Subscription Name: $SUBSCRIPTION_NAME"

echo ""
echo "🔍 Vérification du Resource Group 'E-Commerce'..."

# Vérifier si le resource group existe
if az group show --name "E-Commerce" &> /dev/null; then
    echo "✅ Resource Group 'E-Commerce' trouvé"

    # Obtenir les informations du resource group
    LOCATION=$(az group show --name "E-Commerce" --query location --output tsv)
    echo "📍 Location: $LOCATION"
else
    echo "❌ Resource Group 'E-Commerce' non trouvé"
    echo "💡 Créez-le avec: az group create --name E-Commerce --location 'France Central'"
    echo ""
fi

echo ""
echo "🔍 Vérification de l'App Service 'flam-ecommerce-1754047481'..."

# Vérifier si l'App Service existe
if az webapp show --name "flam-ecommerce-1754047481" --resource-group "E-Commerce" &> /dev/null; then
    echo "✅ App Service 'flam-ecommerce-1754047481' trouvé"

    # Obtenir l'URL de l'app
    APP_URL=$(az webapp show --name "flam-ecommerce-1754047481" --resource-group "E-Commerce" --query hostNames[0] --output tsv)
    echo "🌐 URL: https://$APP_URL"
else
    echo "❌ App Service 'flam-ecommerce-1754047481' non trouvé dans le Resource Group 'E-Commerce'"
    echo "💡 Vérifiez le nom ou créez l'App Service"
fi

echo ""
echo "🔧 Commandes correctes à utiliser:"
echo "=================================="

echo ""
echo "✅ 1. Créer le Service Principal:"
echo "az ad sp create-for-rbac \\"
echo "  --name \"github-actions-ecommerce\" \\"
echo "  --role contributor \\"
echo "  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/E-Commerce \\"
echo "  --sdk-auth"

echo ""
echo "✅ 2. Lister les existing Service Principals:"
echo "az ad sp list --display-name \"github-actions-ecommerce\" --query \"[].{DisplayName:displayName, AppId:appId}\" --output table"

echo ""
echo "✅ 3. Vérifier les permissions (remplacez CLIENT_ID par l'AppId du Service Principal):"
echo "az role assignment list --assignee CLIENT_ID --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/E-Commerce"

echo ""
echo "💾 Ces informations ont été sauvegardées dans azure-info.txt"

# Sauvegarder les informations
cat > azure-info.txt << EOF
# Informations Azure pour votre projet E-Commerce
# Généré le $(date)

SUBSCRIPTION_ID="$SUBSCRIPTION_ID"
TENANT_ID="$TENANT_ID"
SUBSCRIPTION_NAME="$SUBSCRIPTION_NAME"
RESOURCE_GROUP="E-Commerce"
APP_SERVICE_NAME="flam-ecommerce-1754047481"

# Commandes utiles:
# 1. Créer Service Principal:
az ad sp create-for-rbac --name "github-actions-ecommerce" --role contributor --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/E-Commerce --sdk-auth

# 2. Vérifier Service Principals existants:
az ad sp list --display-name "github-actions-ecommerce"

# 3. Vérifier permissions (remplacez CLIENT_ID):
az role assignment list --assignee CLIENT_ID --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/E-Commerce
EOF

echo ""
echo "🚀 Prochaines étapes:"
echo "1. Exécutez la commande '1. Créer Service Principal' ci-dessus"
echo "2. Copiez le JSON retourné"
echo "3. Ajoutez-le comme secret AZURE_CREDENTIALS dans GitHub"
echo "4. Testez le déploiement avec 'git push origin main'"
