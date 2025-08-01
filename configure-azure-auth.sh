#!/bin/bash

# Script pour configurer l'authentification Azure pour GitHub Actions
# Ce script résout l'erreur: "Login failed with Error: Using auth-type: SERVICE_PRINCIPAL"

echo "🔧 Configuration de l'authentification Azure pour GitHub Actions"
echo "============================================================"

# Variables à personnaliser
RESOURCE_GROUP="E-Commerce"
APP_NAME="flam-ecommerce-1754047481"
SUBSCRIPTION_ID="votre-subscription-id"  # À remplacer par votre ID de subscription

echo "📋 Étape 1: Créer un Service Principal Azure"
echo "--------------------------------------------"

# Créer un service principal avec les permissions nécessaires
echo "az ad sp create-for-rbac --name \"github-actions-$APP_NAME\" \\"
echo "  --role contributor \\"
echo "  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \\"
echo "  --sdk-auth"

echo ""
echo "⚠️  IMPORTANT: Exécutez la commande ci-dessus et copiez le JSON retourné"
echo ""

echo "📋 Étape 2: Configurer les secrets GitHub"
echo "----------------------------------------"
echo "Dans votre repository GitHub, allez dans Settings > Secrets and variables > Actions"
echo "et ajoutez les secrets suivants:"
echo ""

echo "🔑 MÉTHODE 1 - Secret unique (recommandé):"
echo "Nom du secret: AZURE_CREDENTIALS"
echo "Valeur: Le JSON complet retourné par la commande az ad sp create-for-rbac"
echo ""

echo "🔑 MÉTHODE 2 - Secrets individuels:"
echo "AZURE_CLIENT_ID=<clientId du JSON>"
echo "AZURE_TENANT_ID=<tenantId du JSON>"
echo "AZURE_SUBSCRIPTION_ID=<subscriptionId du JSON>"
echo "AZURE_CLIENT_SECRET=<clientSecret du JSON>"
echo ""

echo "📋 Étape 3: Vérifier les permissions"
echo "-----------------------------------"
echo "Le service principal doit avoir les permissions suivantes:"
echo "- Contributor sur le Resource Group: $RESOURCE_GROUP"
echo "- Accès en écriture à l'App Service: $APP_NAME"
echo ""

echo "📋 Étape 4: Tester l'authentification"
echo "------------------------------------"
echo "az login --service-principal \\"
echo "  --username <clientId> \\"
echo "  --password <clientSecret> \\"
echo "  --tenant <tenantId>"
echo ""

echo "📋 Exemple de JSON attendu:"
echo "---------------------------"
cat << 'EOF'
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "votre-client-secret",
  "subscriptionId": "12345678-1234-1234-1234-123456789012",
  "tenantId": "12345678-1234-1234-1234-123456789012",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
EOF

echo ""
echo "✅ Une fois ces étapes terminées, votre workflow GitHub Actions pourra"
echo "   s'authentifier correctement avec Azure sans l'erreur SERVICE_PRINCIPAL"
echo ""
echo "🚀 Pour déployer manuellement maintenant:"
echo "   git push origin main"
