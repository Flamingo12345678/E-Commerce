# Guide de Déploiement - YEE E-Commerce sur Digital Ocean

## 📋 Prérequis

1. **Compte Digital Ocean** avec un droplet Ubuntu 22.04
2. **Nom de domaine** pointant vers votre droplet
3. **Repository GitHub** pour votre code
4. **Clés de production** pour Stripe, PayPal, Firebase

## 🚀 Étapes de Déploiement

### 1. Préparation du Repository GitHub

```bash
# Initialiser git si ce n'est pas fait
git init
git add .
git commit -m "Initial commit - E-commerce app ready for deployment"

# Ajouter votre repository GitHub
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
git branch -M main
git push -u origin main
```

### 2. Configuration du Droplet Digital Ocean

#### Connexion au serveur
```bash
ssh root@VOTRE_IP_SERVEUR
```

#### Installation des dépendances
```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation des packages nécessaires
apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib supervisor git certbot python3-certbot-nginx
```

### 3. Configuration de la Base de Données

```bash
# Connexion à PostgreSQL
sudo -u postgres psql

# Création de la base de données
CREATE DATABASE ecommerce_prod;
CREATE USER ecommerce_user WITH PASSWORD 'VOTRE_MOT_DE_PASSE_SECURISE';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_prod TO ecommerce_user;
\q
```

### 4. Déploiement de l'Application

```bash
# Création du répertoire
mkdir -p /opt/app
cd /opt/app

# Clone du repository
git clone https://github.com/VOTRE_USERNAME/VOTRE_REPO.git .

# Configuration de l'environnement Python
python3 -m venv /opt/venv
source /opt/venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt
pip install psycopg2-binary

# Configuration de l'environnement
cp .env.production .env
# IMPORTANT: Éditer le fichier .env avec vos vraies valeurs
nano .env
```

### 5. Configuration Django

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Création du superuser
python manage.py createsuperuser
```

### 6. Configuration Nginx

```bash
# Copie de la configuration
cp nginx.conf /etc/nginx/sites-available/ecommerce
ln -s /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/

# Suppression de la configuration par défaut
rm /etc/nginx/sites-enabled/default

# Test de la configuration
nginx -t

# Redémarrage de Nginx
systemctl restart nginx
```

### 7. Configuration SSL avec Let's Encrypt

```bash
# Installation du certificat SSL
certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Test du renouvellement automatique
certbot renew --dry-run
```

### 8. Configuration Supervisor (Gunicorn)

```bash
# Copie de la configuration
cp supervisor.conf /etc/supervisor/conf.d/ecommerce.conf

# Rechargement de Supervisor
supervisorctl reread
supervisorctl update
supervisorctl start ecommerce
```

### 9. Configuration du Firewall

```bash
# Configuration UFW
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

## 🔧 Maintenance

### Mise à jour de l'application
```bash
cd /opt/app
git pull origin main
source /opt/venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
supervisorctl restart ecommerce
```

### Surveillance des logs
```bash
# Logs de l'application
tail -f /var/log/supervisor/ecommerce.log

# Logs Nginx
tail -f /var/log/nginx/ecommerce_access.log
tail -f /var/log/nginx/ecommerce_error.log
```

## 🛡️ Sécurité

1. **Changez tous les mots de passe par défaut**
2. **Configurez les clés de production** (Stripe, PayPal)
3. **Activez les sauvegardes automatiques** de Digital Ocean
4. **Surveillez les logs** régulièrement
5. **Mettez à jour** le système régulièrement

## 📱 Configuration Mobile/Firebase

Assurez-vous que votre fichier `firebase-credentials.json` est présent sur le serveur dans `/opt/app/firebase-credentials.json`.

## 💳 Tests de Paiement

1. **Stripe**: Utilisez les clés de test d'abord, puis passez en production
2. **PayPal**: Configurez le mode sandbox puis live
3. **Webhooks**: Configurez les URLs de webhook avec votre domaine

## 🚨 Dépannage

### Problèmes courants
- **Erreur 502**: Vérifiez que Gunicorn fonctionne avec `supervisorctl status`
- **Fichiers statiques**: Vérifiez les permissions avec `chown -R www-data:www-data /opt/app`
- **Base de données**: Vérifiez la connexion PostgreSQL

### Commandes utiles
```bash
# Statut des services
systemctl status nginx
supervisorctl status
systemctl status postgresql

# Redémarrage complet
supervisorctl restart ecommerce
systemctl restart nginx
```
