# 🔧 CORRECTIONS PRIORITAIRES - LOGIQUE MÉTIER

## 1. 🚨 CORRECTION CRITIQUE - Template Base (Compteur Panier)

### Problème Actuel
Le template `base.html` affiche un compteur incorrect qui inclut les commandes déjà passées.

### Solution Recommandée

**Étape 1: Créer un template tag personnalisé**

Créer le fichier `store/templatetags/__init__.py`:
```python
# Fichier vide pour faire du dossier un package Python
```

Créer le fichier `store/templatetags/cart_tags.py`:
```python
from django import template
from store.views import get_cart_summary

register = template.Library()

@register.simple_tag
def get_cart_info(user):
    """Retourne les informations du panier pour l'utilisateur"""
    if not user.is_authenticated:
        return {'total_items': 0, 'total_price': 0, 'is_empty': True}
    
    return get_cart_summary(user)
```

**Étape 2: Modifier le template base.html**
```django
{% load cart_tags %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>YEE E-Commerce</title>
</head>
<body>
    <a href="{% url 'index' %}">
        <h1>Bienvenue chez YEE</h1>
    </a>

    {% if user.is_authenticated %}
        {{ user.display_name }} 
        <a href="{% url 'profile' %}">Mon profil</a> |
        <a href="{% url 'logout' %}">Se déconnecter</a>
        
        {% get_cart_info user as cart_info %}
        {% if not cart_info.is_empty %}
            <p>
                <a href="{% url 'cart' %}">
                    Mon panier ({{ cart_info.total_items }}) - {{ cart_info.total_price }} €
                </a>
            </p>
        {% endif %}
    {% else %}
        <a href="{% url 'login' %}">Connexion</a>
        <a href="{% url 'signup' %}">S'inscrire</a>
    {% endif %}

    <!-- Affichage des messages -->
    {% if messages %}
        <div class="messages">
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">
                    {{ message }}
                </div>
            {% endfor %}
        </div>
    {% endif %}

    {% block content %}
    {% endblock content %}
</body>
</html>
```

---

## 2. 🚨 CORRECTION CRITIQUE - Gestion de Stock

### Problème Actuel
Pas de vérification appropriée du stock lors de l'augmentation de quantité.

### Solution: Améliorer la fonction increase_quantity

```python
def increase_quantity(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Vous devez être connecté.")
        return redirect("login")

    try:
        with transaction.atomic():
            order = get_object_or_404(
                Order, 
                id=order_id, 
                user=request.user, 
                ordered=False
            )

            # Vérifier le stock disponible
            if order.quantity >= order.product.stock:
                messages.warning(
                    request,
                    f"Stock insuffisant pour '{order.product.name}'. "
                    f"Stock disponible: {order.product.stock}"
                )
            else:
                order.quantity += 1
                order.save()
                messages.success(
                    request,
                    f"Quantité de '{order.product.name}' "
                    f"augmentée à {order.quantity}."
                )

    except Order.DoesNotExist:
        messages.error(request, "Produit non trouvé dans votre panier.")
    except Exception as e:
        messages.error(
            request, 
            "Erreur lors de la modification de la quantité."
        )
        # Log l'erreur pour debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur increase_quantity: {e}")

    return redirect("cart")
```

---

## 3. ⚠️ AMÉLIORATION MAJEURE - Validation Add to Cart

### Problème Actuel
La fonction `add_to_cart` ne gère pas tous les cas edge.

### Solution: Améliorer add_to_cart

```python
def add_to_cart(request, slug):
    if not request.user.is_authenticated:
        messages.warning(
            request, 
            "Vous devez être connecté pour ajouter des produits au panier."
        )
        return redirect("login")

    try:
        with transaction.atomic():
            user = request.user
            product = get_object_or_404(Product, slug=slug)

            # Vérifier le stock disponible
            if product.stock <= 0:
                messages.error(
                    request, 
                    f"Le produit '{product.name}' n'est plus en stock."
                )
                return redirect(reverse("product", kwargs={"slug": slug}))

            # Créer ou récupérer le panier
            cart_obj, _ = Cart.objects.get_or_create(user=user)

            # Chercher une commande existante pour ce produit
            existing_order = cart_obj.orders.filter(
                product=product, 
                ordered=False
            ).first()

            if existing_order:
                # Le produit est déjà dans le panier
                if existing_order.quantity >= product.stock:
                    messages.warning(
                        request,
                        f"Vous avez déjà le maximum disponible de "
                        f"'{product.name}' dans votre panier."
                    )
                else:
                    # Augmenter la quantité si possible
                    existing_order.quantity += 1
                    existing_order.save()
                    messages.success(
                        request,
                        f"Quantité de '{product.name}' augmentée à "
                        f"{existing_order.quantity}."
                    )
            else:
                # Créer une nouvelle commande
                order = Order.objects.create(
                    user=user, 
                    product=product, 
                    quantity=1, 
                    ordered=False
                )
                cart_obj.orders.add(order)
                messages.success(
                    request, 
                    f"'{product.name}' a été ajouté à votre panier !"
                )

    except Product.DoesNotExist:
        messages.error(request, "Produit introuvable.")
    except IntegrityError:
        messages.error(request, "Erreur de données lors de l'ajout au panier.")
    except Exception as e:
        messages.error(request, "Erreur inattendue lors de l'ajout au panier.")
        # Log pour debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur add_to_cart: {e}")

    return redirect(reverse("product", kwargs={"slug": slug}))
```

---

## 4. 🔧 AMÉLIORATION - Optimisation des Requêtes

### Solution: Optimiser les vues avec select_related

```python
def cart(request):
    if not request.user.is_authenticated:
        messages.warning(
            request, 
            "Vous devez être connecté pour voir votre panier."
        )
        return redirect("login")

    # Optimisation avec select_related et prefetch_related
    try:
        cart_obj = Cart.objects.select_related('user').prefetch_related(
            'orders__product'
        ).get(user=request.user)
        
        orders = cart_obj.orders.filter(ordered=False).select_related('product')
        
    except Cart.DoesNotExist:
        orders = []
        cart_obj = None

    # Calculer les totaux de manière optimisée
    total_items = sum(order.quantity for order in orders)
    total_price = sum(order.total_price for order in orders)

    context = {
        "orders": orders,
        "total": total_price,
        "total_items": total_items,
        "is_empty": not orders,
        "cart": cart_obj,
    }
    return render(request, "store/cart.html", context)
```

---

## 5. 📝 AMÉLIORATION - Logging et Monitoring

### Solution: Ajouter dans settings.py

```python
# Ajouter à la fin de settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'store.views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'accounts.views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Sécurité supplémentaire
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 📋 ORDRE D'IMPLÉMENTATION

1. **URGENT (Aujourd'hui)**
   - [ ] Créer le template tag pour le panier
   - [ ] Modifier base.html
   - [ ] Tester le compteur de panier

2. **CRITIQUE (Demain)**
   - [ ] Améliorer increase_quantity()
   - [ ] Améliorer add_to_cart()
   - [ ] Tester gestion de stock

3. **IMPORTANT (Cette semaine)**
   - [ ] Optimiser les requêtes
   - [ ] Ajouter logging
   - [ ] Tests complets

4. **SUIVI (Semaine suivante)**
   - [ ] Monitoring des performances
   - [ ] Analyse des logs
   - [ ] Optimisations supplémentaires

---

## ✅ VALIDATION

Après chaque correction, tester:

1. **Compteur panier**: Vérifier affichage correct
2. **Gestion stock**: Tester limites et erreurs
3. **Performance**: Vérifier temps de réponse
4. **Logs**: Vérifier enregistrement des erreurs
5. **UX**: Tester parcours utilisateur complet

---

*Corrections prioritaires identifiées le 14 juillet 2025*
