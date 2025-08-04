#!/bin/bash

# Script de déploiement automatisé pour DigitalOcean App Platform
# Domaine: y-e-e.codes

echo "🚀 Préparation du déploiement pour y-e-e.codes sur DigitalOcean App Platform"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Vérifier la présence des fichiers essentiels
echo "📋 Vérification des fichiers de configuration..."

if [ ! -f ".do/app.yaml" ]; then
    echo "❌ Fichier .do/app.yaml manquant"
    exit 1
else
    echo "✅ Fichier .do/app.yaml présent"
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Fichier requirements.txt manquant"
    exit 1
else
    echo "✅ Fichier requirements.txt présent"
fi

if [ ! -f "shop/settings.py" ]; then
    echo "❌ Fichier shop/settings.py manquant"
    exit 1
else
    echo "✅ Fichier shop/settings.py présent"
fi

# Générer une clé secrète Django pour production
echo "🔐 Génération d'une clé secrète Django sécurisée..."
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo "📝 Clé secrète générée: $SECRET_KEY"
echo "⚠️  Copiez cette clé et configurez-la comme variable d'environnement SECRET_KEY dans DigitalOcean"

# Vérifier les dépendances
echo "📦 Vérification des dépendances critiques..."
python -c "import django; print(f'✅ Django {django.get_version()}')" 2>/dev/null || echo "❌ Django non installé"
python -c "import gunicorn; print('✅ Gunicorn installé')" 2>/dev/null || echo "❌ Gunicorn non installé"
python -c "import psycopg2; print('✅ PostgreSQL adapter installé')" 2>/dev/null || echo "❌ psycopg2-binary non installé"

# Tester les settings Django
echo "⚙️ Test de la configuration Django..."
python manage.py check --deploy --settings=shop.settings 2>/dev/null && echo "✅ Configuration Django valide" || echo "⚠️ Problèmes de configuration détectés"

# Instructions finales
echo ""
echo "🎯 ÉTAPES SUIVANTES POUR LE DÉPLOIEMENT:"
echo "======================================"
echo ""
echo "1. 📁 Pousser le code sur GitHub:"
echo "   git add ."
echo "   git commit -m 'Configuration App Platform pour y-e-e.codes'"
echo "   git push origin main"
echo ""
echo "2. 🌐 Créer l'app sur DigitalOcean:"
echo "   - Aller sur https://cloud.digitalocean.com/apps"
echo "   - Create App > GitHub > Sélectionner votre repo"
echo "   - Le fichier .do/app.yaml sera détecté automatiquement"
echo ""
echo "3. 🔑 Configurer les variables d'environnement:"
echo "   SECRET_KEY: $SECRET_KEY"
echo "   STRIPE_PUBLISHABLE_KEY: [votre clé Stripe]"
echo "   STRIPE_SECRET_KEY: [votre clé secrète Stripe]"
echo "   STRIPE_WEBHOOK_SECRET: [votre webhook secret]"
echo "   PAYPAL_CLIENT_ID: [votre ID PayPal]"
echo "   PAYPAL_CLIENT_SECRET: [votre secret PayPal]"
echo "   EMAIL_HOST_USER: [votre email]"
echo "   EMAIL_HOST_PASSWORD: [mot de passe app email]"
echo "   FIREBASE_CREDENTIALS: [contenu du fichier firebase-credentials.json]"
echo ""
echo "4. 🌍 Configurer DNS chez Name.com:"
echo "   - Obtenir l'IP depuis DigitalOcean après déploiement"
echo "   - Ajouter enregistrement A: @ -> [IP DigitalOcean]"
echo "   - Ajouter enregistrement CNAME: www -> y-e-e.codes"
echo ""
echo "5. ✅ Post-déploiement:"
echo "   - Aller dans App Platform > Console"
echo "   - Exécuter: python manage.py migrate"
echo "   - Exécuter: python manage.py createsuperuser"
echo ""
echo "🎉 Votre site sera accessible sur https://y-e-e.codes une fois le DNS configuré!"
