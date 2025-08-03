# 🚀 Déploiement Rapide sur Digital Ocean

## Déploiement en Une Commande

Une fois votre droplet Digital Ocean créé et votre domaine configuré, exécutez simplement :

```bash
./deploy-to-digitalocean.sh
```

Ce script va automatiquement :
- ✅ Pousser votre code sur GitHub
- ✅ Configurer le serveur Digital Ocean
- ✅ Installer toutes les dépendances
- ✅ Configurer PostgreSQL
- ✅ Déployer l'application Django
- ✅ Configurer Nginx et SSL
- ✅ Démarrer tous les services

## Checklist Avant Déploiement

### 1. Digital Ocean
- [ ] Droplet Ubuntu 22.04 créé
- [ ] IP publique notée
- [ ] Accès SSH configuré

### 2. Domaine
- [ ] Nom de domaine acheté
- [ ] DNS pointant vers l'IP du droplet
- [ ] Sous-domaine www configuré

### 3. GitHub
- [ ] Repository GitHub créé
- [ ] Code poussé sur la branche main
- [ ] Accès en lecture publique ou clés SSH configurées

### 4. Clés de Production
- [ ] Clés Stripe de production obtenues
- [ ] Compte PayPal Business configuré
- [ ] Credentials Firebase préparés
- [ ] Email SMTP configuré

## Configuration Post-Déploiement

### 1. Créer un Super Utilisateur
```bash
ssh root@VOTRE_IP
cd /opt/app
source /opt/venv/bin/activate
python manage.py createsuperuser
```

### 2. Configurer les Clés de Production
```bash
nano /opt/app/.env
```

Modifiez les valeurs suivantes :
```
# Stripe Production
STRIPE_PUBLISHABLE_KEY=pk_live_VOTRE_CLE
STRIPE_SECRET_KEY=sk_live_VOTRE_CLE
STRIPE_WEBHOOK_SECRET=whsec_VOTRE_WEBHOOK

# PayPal Production
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=VOTRE_CLIENT_ID
PAYPAL_CLIENT_SECRET=VOTRE_SECRET

# Email Production
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=mot_de_passe_app
```

### 3. Redémarrer les Services
```bash
supervisorctl restart ecommerce
systemctl reload nginx
```

## Tests de Fonctionnement

1. **Site Web** : `https://votre-domaine.com`
2. **Administration** : `https://votre-domaine.com/admin/`
3. **Test de Paiement** : Effectuer un achat test
4. **SSL** : Vérifier le certificat HTTPS

## Maintenance

### Mise à Jour de l'Application
```bash
cd /opt/app
git pull origin main
source /opt/venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
supervisorctl restart ecommerce
```

### Surveillance des Logs
```bash
# Logs de l'application
tail -f /var/log/supervisor/ecommerce.log

# Logs Nginx
tail -f /var/log/nginx/ecommerce_access.log
tail -f /var/log/nginx/ecommerce_error.log
```

### Sauvegarde de la Base de Données
```bash
sudo -u postgres pg_dump ecommerce_prod > backup_$(date +%Y%m%d).sql
```

## Support

En cas de problème, vérifiez :
1. Les logs avec les commandes ci-dessus
2. Le statut des services : `systemctl status nginx` et `supervisorctl status`
3. La configuration DNS de votre domaine
4. Les permissions des fichiers : `chown -R www-data:www-data /opt/app`

## Sécurité

- 🔒 SSL automatiquement configuré avec Let's Encrypt
- 🔥 Firewall UFW activé
- 🛡️ Headers de sécurité configurés dans Nginx
- 🗄️ Base de données PostgreSQL sécurisée
- 🔐 Variables d'environnement protégées
