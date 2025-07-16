# 🧾 Système de Facturation - Guide Complet

## 📋 Vue d'ensemble

Le système de facturation intégré utilise les APIs de Stripe et PayPal pour créer, gérer et traiter les factures. Il inclut :

- **Facturation automatisée** avec Stripe et PayPal
- **Factures récurrentes** avec gestion des échéances
- **Templates de factures** personnalisables
- **Suivi des paiements** en temps réel
- **Interface d'administration** complète
- **Rappels automatiques** pour les factures impayées

## 🏗️ Architecture

### Modèles principaux

1. **InvoiceTemplate** - Templates de factures réutilisables
2. **Invoice** - Factures individuelles 
3. **InvoiceItem** - Articles/services sur les factures
4. **InvoicePayment** - Suivi des paiements
5. **InvoiceReminder** - Rappels automatiques
6. **RecurringInvoiceTemplate** - Facturation récurrente

### Services intégrés

1. **StripeInvoiceService** - Gestion Stripe
2. **PayPalInvoiceService** - Gestion PayPal  
3. **InvoiceManager** - Coordination générale

## ⚙️ Configuration

### 1. Variables d'environnement

Ajoutez dans votre fichier `.env` ou `settings.py` :

```python
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
STRIPE_WEBHOOK_SECRET = 'whsec_...'

# PayPal Configuration  
PAYPAL_CLIENT_ID = 'your_paypal_client_id'
PAYPAL_CLIENT_SECRET = 'your_paypal_client_secret'
PAYPAL_MODE = 'sandbox'  # ou 'live' pour la production

# URL de base pour les webhooks
BASE_URL = 'https://votre-domaine.com'
```

### 2. Installation des dépendances

```bash
pip install stripe paypal-checkout-serversdk python-dateutil
```

### 3. Configuration des webhooks

#### Stripe
1. Allez dans votre dashboard Stripe
2. Section "Developers" > "Webhooks"
3. Ajoutez un endpoint : `https://votre-domaine.com/accounts/webhooks/stripe/`
4. Événements à écouter :
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `invoice.finalized`

#### PayPal
1. Accédez à votre tableau de bord PayPal Developer
2. Créez une application ou modifiez existante
3. Ajoutez webhook URL : `https://votre-domaine.com/accounts/webhooks/paypal/`
4. Événements à écouter :
   - `INVOICING.INVOICE.PAID`
   - `INVOICING.INVOICE.CANCELLED`

## 🚀 Utilisation

### 1. Créer une facture via l'interface d'administration

1. Connectez-vous à l'admin Django : `/admin/`
2. Section "Accounts" > "Invoices"
3. Cliquez "Ajouter Invoice"
4. Remplissez les informations client
5. Ajoutez les articles via les "Invoice items"
6. Choisissez le fournisseur (Stripe/PayPal)
7. Sauvegardez

### 2. Créer une facture programmatiquement

```python
from accounts.invoice_services import InvoiceManager
from accounts.models import Shopper

# Récupérer le client
customer = Shopper.objects.get(email='client@example.com')

# Créer la facture
invoice_manager = InvoiceManager()
invoice = invoice_manager.create_invoice(
    customer=customer,
    provider='stripe',  # ou 'paypal'
    items=[
        {
            'description': 'Service consultation',
            'quantity': 1,
            'unit_price': 150.00
        },
        {
            'description': 'Formation',
            'quantity': 2, 
            'unit_price': 75.00
        }
    ],
    due_date='2025-02-15',
    notes='Merci pour votre confiance'
)

# Envoyer la facture
result = invoice_manager.send_invoice(invoice.id)
```

### 3. Facturation récurrente

```python
from accounts.invoice_services import InvoiceManager
from accounts.models import RecurringInvoiceTemplate

# Créer un template récurrent
template = RecurringInvoiceTemplate.objects.create(
    customer=customer,
    provider='stripe',
    frequency='monthly',
    amount=99.00,
    description='Abonnement mensuel',
    start_date='2025-01-01',
    end_date='2025-12-31'
)

# Le système créera automatiquement les factures selon la fréquence
```

### 4. Commande de gestion

Pour traiter les factures récurrentes automatiquement :

```bash
# À exécuter régulièrement (par exemple via cron)
python manage.py process_invoices
```

Ajoutez dans votre crontab :
```bash
# Tous les jours à 9h
0 9 * * * /path/to/your/project/env/bin/python /path/to/manage.py process_invoices
```

## 📊 Interface d'administration

### Fonctionnalités disponibles

#### Liste des factures
- **Filtrage** par statut, client, fournisseur, dates
- **Recherche** par numéro, client, description
- **Actions en lot** : envoyer, marquer comme payée, etc.
- **Export** des données

#### Détail de facture
- **Informations complètes** sur la facture
- **Historique des paiements**
- **Rappels envoyés**
- **Logs d'activité**
- **Actions directes** : envoyer, rembourser, etc.

#### Templates de factures
- **Gestion centralisée** des modèles
- **Personnalisation** du design
- **Variables dynamiques** pour la personnalisation

#### Facturation récurrente
- **Configuration** des abonnements
- **Suivi** des générations automatiques
- **Gestion** des échecs et reprises

## 🔧 Personnalisation

### 1. Templates HTML

Modifiez les templates dans `templates/accounts/invoices/` :

- `list.html` - Liste des factures client
- `detail.html` - Détail d'une facture  
- `pay.html` - Page de paiement

### 2. Styles CSS

Personnalisez l'apparence en modifiant les classes Tailwind CSS dans les templates.

### 3. Logique métier

Étendez les services dans `accounts/invoice_services.py` :

```python
class CustomInvoiceManager(InvoiceManager):
    def custom_logic(self):
        # Votre logique personnalisée
        pass
```

## 🔍 Debugging et logs

### 1. Logs Django

Les logs sont configurés dans `settings.py`. Vérifiez :

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'accounts.invoice_services': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. Tests de webhooks

Utilisez les scripts de debug fournis :

```bash
# Test des signatures Stripe
python test_stripe_signature.py

# Debug général des webhooks  
python debug_webhooks.py
```

### 3. Interface d'administration - WebhookLog

Surveillez les webhooks dans l'admin Django :
- Section "Accounts" > "Webhook logs"
- Vérifiez les signatures et traitements
- Rejouer les webhooks échoués

## 🛡️ Sécurité

### 1. Validation des webhooks

- **Stripe** : Validation HMAC-SHA256
- **PayPal** : Validation des certificats et signatures

### 2. Gestion des erreurs

- **Retry automatique** pour les webhooks échoués
- **Logs détaillés** de toutes les opérations
- **Alertes** en cas d'erreurs critiques

### 3. Accès et permissions

- **Interface admin** sécurisée par Django
- **API endpoints** avec authentification requise
- **Logs d'audit** pour toutes les actions

## 📈 Monitoring et métriques

### 1. Métriques disponibles

- **Revenus** par période
- **Taux de paiement** des factures
- **Performance** des fournisseurs
- **Temps de traitement** des webhooks

### 2. Rapports

Générez des rapports via l'interface admin ou programmatiquement :

```python
from accounts.models import Invoice
from django.db.models import Sum, Count

# Rapport mensuel
monthly_report = Invoice.objects.filter(
    created_at__month=1,
    created_at__year=2025
).aggregate(
    total_amount=Sum('total_amount'),
    count=Count('id'),
    paid_count=Count('id', filter=models.Q(status='paid'))
)
```

## 🔄 Maintenance

### 1. Nettoyage régulier

```bash
# Nettoyer les anciens logs (>30 jours)
python manage.py shell -c "
from accounts.models import WebhookLog
from django.utils import timezone
from datetime import timedelta
WebhookLog.objects.filter(
    received_at__lt=timezone.now() - timedelta(days=30)
).delete()
"
```

### 2. Synchronisation

Synchronisez périodiquement avec les fournisseurs :

```python
from accounts.invoice_services import InvoiceManager

manager = InvoiceManager()
manager.sync_with_providers()  # À implémenter selon besoins
```

## 🆘 Dépannage

### Problèmes courants

1. **Webhooks non reçus**
   - Vérifiez les URLs de webhook
   - Contrôlez les certificats SSL
   - Testez la connectivité réseau

2. **Erreurs de paiement**
   - Vérifiez les clés API
   - Contrôlez les limites de compte
   - Vérifiez les devises supportées

3. **Factures non générées**
   - Vérifiez la commande cron
   - Contrôlez les templates récurrents
   - Vérifiez les logs d'erreur

### Support

En cas de problème :
1. Vérifiez les logs Django
2. Consultez les WebhookLogs dans l'admin
3. Testez avec les outils de debug fournis
4. Consultez la documentation officielle Stripe/PayPal

---

🎉 **Félicitations !** Votre système de facturation est maintenant opérationnel. Vous pouvez créer, gérer et traiter des factures avec Stripe et PayPal de manière professionnelle et automatisée.
