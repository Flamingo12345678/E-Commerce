#!/bin/bash

# Script de déploiement automatique pour Digital Ocean
# Usage: ./deploy-to-digitalocean.sh

set -e

echo "🚀 Déploiement YEE E-Commerce sur Digital Ocean"
echo "================================================"

# Variables à configurer
read -p "Entrez l'IP de votre serveur Digital Ocean: " SERVER_IP
read -p "Entrez votre nom d'utilisateur GitHub: " GITHUB_USERNAME
read -p "Entrez le nom de votre repository: " REPO_NAME
read -p "Entrez votre nom de domaine (ex: monsite.com): " DOMAIN_NAME

REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

echo ""
echo "Configuration:"
echo "- Serveur: $SERVER_IP"
echo "- Repository: $REPO_URL"
echo "- Domaine: $DOMAIN_NAME"
echo ""

read -p "Continuer avec cette configuration? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Déploiement annulé."
    exit 1
fi

# Étape 1: Pousser le code sur GitHub
echo "📤 Push du code sur GitHub..."
git push origin main

# Étape 2: Connexion au serveur et déploiement
echo "🔗 Connexion au serveur Digital Ocean..."

ssh root@$SERVER_IP << EOF
    # Mise à jour du système
    echo "📦 Mise à jour du système..."
    apt update && apt upgrade -y

    # Installation des dépendances
    echo "🛠️ Installation des dépendances..."
    apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib supervisor git certbot python3-certbot-nginx ufw

    # Configuration du firewall
    echo "🔥 Configuration du firewall..."
    ufw allow OpenSSH
    ufw allow 'Nginx Full'
    ufw --force enable

    # Configuration PostgreSQL
    echo "🗄️ Configuration PostgreSQL..."
    sudo -u postgres psql -c "CREATE DATABASE ecommerce_prod;" || true
    sudo -u postgres psql -c "CREATE USER ecommerce_user WITH PASSWORD 'EcommerceSecure2024!';" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecommerce_prod TO ecommerce_user;" || true

    # Clone du repository
    echo "📥 Clone du repository..."
    rm -rf /opt/app
    mkdir -p /opt/app
    cd /opt/app
    git clone $REPO_URL .

    # Configuration Python
    echo "🐍 Configuration Python..."
    python3 -m venv /opt/venv
    source /opt/venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install psycopg2-binary

    # Configuration des variables d'environnement
    echo "⚙️ Configuration de l'environnement..."
    cp .env.production .env

    # Personnalisation du fichier .env
    sed -i "s/votre-domaine.com/$DOMAIN_NAME/g" .env
    sed -i "s/VOTRE_MOT_DE_PASSE_DB/EcommerceSecure2024!/g" .env
    sed -i "s/DB_ENGINE=postgresql/DB_ENGINE=postgresql/g" .env

    # Migrations Django
    echo "🗂️ Migrations Django..."
    python manage.py makemigrations
    python manage.py migrate

    # Collecte des fichiers statiques
    echo "📄 Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput

    # Configuration des permissions
    echo "🔐 Configuration des permissions..."
    chown -R www-data:www-data /opt/app
    chmod +x /opt/app/deploy.sh

    # Configuration Nginx
    echo "🌐 Configuration Nginx..."
    sed -i "s/votre-domaine.com/$DOMAIN_NAME/g" /opt/app/nginx.conf
    cp /opt/app/nginx.conf /etc/nginx/sites-available/ecommerce
    ln -sf /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl restart nginx

    # Configuration Supervisor
    echo "⚡ Configuration Supervisor..."
    cp /opt/app/supervisor.conf /etc/supervisor/conf.d/ecommerce.conf
    supervisorctl reread
    supervisorctl update
    supervisorctl start ecommerce

    # Configuration SSL
    echo "🔒 Configuration SSL..."
    certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME

    echo "✅ Déploiement terminé!"
    echo "🌍 Votre site est accessible sur: https://$DOMAIN_NAME"
    echo "🔧 Admin: https://$DOMAIN_NAME/admin/"

    # Affichage des statuts
    echo ""
    echo "📊 Statuts des services:"
    systemctl status nginx --no-pager -l
    supervisorctl status

EOF

echo ""
echo "🎉 Déploiement terminé avec succès!"
echo "🌍 Votre site: https://$DOMAIN_NAME"
echo "🔧 Administration: https://$DOMAIN_NAME/admin/"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Configurez vos clés de production Stripe/PayPal dans le fichier .env sur le serveur"
echo "2. Créez un superuser: ssh root@$SERVER_IP 'cd /opt/app && source /opt/venv/bin/activate && python manage.py createsuperuser'"
echo "3. Testez les paiements en mode sandbox puis passez en production"
