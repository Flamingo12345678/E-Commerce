# ✅ Checklist de Vérification DNS pour y-e-e.codes

## Configuration DNS chez Name.com

Avant de déployer sur DigitalOcean App Platform, vérifiez que ces enregistrements DNS sont correctement configurés chez Name.com :

### Enregistrements DNS Requis :

```
Type    Nom    Valeur                                  TTL    Priorité
A       @      [IP fournie par DigitalOcean]          300    -
CNAME   www    y-e-e.codes                            300    -
```

### Vérification DNS en ligne :

1. **Outils de vérification DNS :**
   - https://dnschecker.org/
   - https://www.whatsmydns.net/
   - `nslookup y-e-e.codes`
   - `dig y-e-e.codes`

2. **Commandes de test locales :**
```bash
# Vérifier l'enregistrement A
nslookup y-e-e.codes

# Vérifier l'enregistrement CNAME pour www
nslookup www.y-e-e.codes

# Test avec dig
dig y-e-e.codes
dig www.y-e-e.codes
```

## Étapes de Configuration :

### 1. Déployer d'abord sur DigitalOcean
- L'app sera accessible sur : `https://yee-ecommerce-xxxxx.ondigitalocean.app`
- DigitalOcean vous fournira l'IP à utiliser

### 2. Configurer DNS chez Name.com
- Aller dans la section DNS de Name.com
- Ajouter les enregistrements ci-dessus avec l'IP fournie

### 3. Attendre la propagation DNS
- Propagation : 5-60 minutes généralement
- Vérifier avec les outils en ligne

### 4. Ajouter le domaine dans DigitalOcean App Platform
- Aller dans Settings > Domains
- Ajouter y-e-e.codes comme domaine principal
- Ajouter www.y-e-e.codes comme alias
- SSL sera automatiquement configuré

## Vérification Post-Déploiement :

✅ `https://y-e-e.codes` - Doit rediriger vers HTTPS
✅ `https://www.y-e-e.codes` - Doit rediriger vers y-e-e.codes
✅ Certificat SSL valide
✅ Toutes les pages fonctionnent
✅ Paiements Stripe/PayPal opérationnels
✅ Administration accessible

## En cas de problème :

### DNS ne résout pas :
- Vérifier les enregistrements chez Name.com
- Attendre plus longtemps (jusqu'à 24h max)
- Contacter le support Name.com si nécessaire

### SSL non valide :
- DigitalOcean génère automatiquement via Let's Encrypt
- Peut prendre 10-15 minutes après configuration DNS
- Vérifier que le domaine pointe bien vers DigitalOcean

### Site inaccessible :
- Vérifier les logs dans l'interface DigitalOcean
- S'assurer que les variables d'environnement sont configurées
- Vérifier que les migrations ont été exécutées
