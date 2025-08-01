#!/bin/bash

# Script pour créer un nouveau secret pour le Service Principal existant
# Cela résoudra votre problème d'authentification GitHub Actions

echo "🔐 Création d'un nouveau secret pour le Service Principal existant"
echo "=================================================================="

# Informations de votre Service Principal existant
SP_APP_ID="a194419e-b887-478d-982f-e20218de7e13"
SUBSCRIPTION_ID="727244c5-82e1-458c-812f-42c50e7f25f3"
TENANT_ID="7db2a10b-00d1-4bcf-9ed9-3956e0999700"

echo "📋 Service Principal détecté:"
echo "   App ID: $SP_APP_ID"
echo "   Display Name: github-actions-ecommerce"
echo "   Permissions: Contributor sur E-Commerce ✅"
echo ""

echo "🔑 Création d'un nouveau secret..."
echo "Cette opération va créer un nouveau clientSecret pour votre Service Principal existant"
echo ""

# Créer un nouveau secret pour le Service Principal existant (syntaxe corrigée)
echo "Exécution de la commande:"
echo "az ad sp credential reset --id $SP_APP_ID --years 2"
echo ""

# Exécuter la commande avec la bonne syntaxe
az ad sp credential reset --id $SP_APP_ID --years 2 > sp_credentials.json

if [ $? -eq 0 ]; then
    echo "✅ Nouveau secret créé avec succès!"
    echo ""

    # Lire le résultat
    CLIENT_SECRET=$(cat sp_credentials.json | grep '"password"' | cut -d'"' -f4)

    echo "📋 Voici votre JSON pour GitHub Actions:"
    echo "========================================"

    # Créer le JSON complet pour GitHub Actions
    cat > azure_credentials.json << EOF
{
  "clientId": "$SP_APP_ID",
  "clientSecret": "$CLIENT_SECRET",
  "subscriptionId": "$SUBSCRIPTION_ID",
  "tenantId": "$TENANT_ID",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
EOF

    echo ""
    echo "💾 JSON sauvegardé dans azure_credentials.json"
    echo ""
    echo "🔑 COPIEZ LE CONTENU CI-DESSOUS POUR GITHUB ACTIONS:"
    echo "=================================================="
    cat azure_credentials.json
    echo "=================================================="
    echo ""

    echo "📝 Prochaines étapes:"
    echo "1. 📋 Copiez le JSON ci-dessus"
    echo "2. 🌐 Allez sur GitHub.com → Votre repository → Settings"
    echo "3. 🔐 Secrets and variables → Actions"
    echo "4. ➕ New repository secret"
    echo "5. 📝 Name: AZURE_CREDENTIALS"
    echo "6. 📋 Value: Collez le JSON complet"
    echo "7. 💾 Add secret"
    echo "8. 🚀 git push origin main (pour tester le déploiement)"
    echo ""

    # Nettoyer le fichier temporaire
    rm sp_credentials.json

else
    echo "❌ Erreur lors de la création du secret"
    echo "💡 Vérifiez que vous êtes bien connecté: az account show"
    echo "💡 Si nécessaire, reconnectez-vous: az login"

    # Afficher le contenu du fichier d'erreur s'il existe
    if [ -f sp_credentials.json ]; then
        echo "🔍 Détails de l'erreur:"
        cat sp_credentials.json
        rm sp_credentials.json
    fi
fi

echo ""
echo "🧪 Pour tester l'authentification localement:"
echo "az login --service-principal --username $SP_APP_ID --password [LE_CLIENT_SECRET] --tenant $TENANT_ID"
