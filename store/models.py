from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
from django.urls import reverse
from shop.settings import AUTH_USER_MODEL


# Category model for organizing products
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Nouveaux champs pour améliorer la logique métier
    is_featured = models.BooleanField(
        default=False, help_text="Afficher sur la page d'accueil"
    )
    display_order = models.PositiveIntegerField(
        default=0, help_text="Ordre d'affichage (0 = premier)"
    )
    is_active = models.BooleanField(
        default=True, help_text="Catégorie active et visible"
    )
    color_theme = models.CharField(
        max_length=7, default="#6c757d", help_text="Couleur thème en hexa (#ffffff)"
    )
    icon_class = models.CharField(
        max_length=50, blank=True, help_text="Classe CSS de l'icône (ex: fas fa-tshirt)"
    )

    # SEO et métadonnées
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="Description pour SEO"
    )
    meta_keywords = models.CharField(
        max_length=255, blank=True, help_text="Mots-clés SEO séparés par des virgules"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return str(self.name)

    @property
    def product_count(self):
        """Nombre de produits en stock dans cette catégorie"""
        return (
            Product.objects.filter(category=self, variants__stock__gt=0)
            .distinct()
            .count()
        )

    @property
    def total_product_count(self):
        """Nombre total de produits (incluant rupture de stock)"""
        return Product.objects.filter(category=self).count()

    def get_absolute_url(self):
        """URL de la catégorie"""
        return reverse("category", kwargs={"category_slug": self.slug})

    @property
    def background_gradient(self):
        """Génère un gradient CSS basé sur la couleur thème"""
        import colorsys

        # Convertir hex en RGB
        hex_color = str(self.color_theme).lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        # Convertir en HSL pour éclaircir
        h, l, s = colorsys.rgb_to_hls(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)

        # Créer une version plus claire
        lighter_rgb = colorsys.hls_to_rgb(h, min(1, l + 0.2), s)
        lighter_hex = "#" + "".join(f"{int(c*255):02x}" for c in lighter_rgb)

        return f"linear-gradient(135deg, {self.color_theme}, " f"{lighter_hex})"


# products
# -Nom
# -Prix
# -Description
# -Quantité en stock
# -Image


class Product(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="products/", blank=True, null=True)
    shoe_size = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Pointure de chaussure (ex: 38.5)",
    )

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    rating = models.FloatField(default=0)  # note moyenne sur 5
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def is_available(self):
        """Vérifie si le produit est disponible en stock via ses variantes"""
        return self.variants.filter(stock__gt=0).exists()

    @property
    def total_stock(self):
        """Retourne le stock total de toutes les variantes"""
        return sum(variant.stock for variant in self.variants.all())

    @property
    def formatted_price(self):
        """Retourne le prix formaté"""
        return f"{self.price:.2f} €"

    def get_variant_by_size(self, size):
        """Retourne la variante correspondant à la taille donnée"""
        if not size:
            # Si pas de taille spécifiée, retourner la première variante disponible
            return self.variants.filter(stock__gt=0).first()
        return self.variants.filter(size=size).first()

    def reduce_stock(self, size, quantity):
        """
        Réduit le stock de la variante correspondante
        Retourne True si réussi, False sinon
        """
        variant = self.get_variant_by_size(size)
        if variant and variant.stock >= quantity:
            variant.stock -= quantity
            variant.save()
            return True
        return False

    def get_stock_for_size(self, size):
        """Retourne le stock disponible pour une taille donnée"""
        variant = self.get_variant_by_size(size)
        return variant.stock if variant else 0


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    size = models.CharField(max_length=8)
    stock = models.IntegerField(default=0)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Prix spécifique à la variante (optionnel)",
    )

    class Meta:
        unique_together = ("product", "size")
        verbose_name = "Variante de produit"
        verbose_name_plural = "Variantes de produit"

    def __str__(self):
        return f"{self.product.name} - {self.size}"


# Invalidation du cache des produits vedettes à chaque modification ou suppression d'un produit
@receiver([post_save, post_delete], sender=Product)
def invalidate_featured_products_cache(sender, instance, **kwargs):
    for limit in [10, 20, 50]:
        cache_key = f"featured_products_{limit}"
        cache.delete(cache_key)


# Articles (Orders)

# - Utilisateur
# - Produit
# - Quantité
# - Commandé ou non


class Order(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    size = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Taille sélectionnée (ex: M, 42, Unique)",
    )
    ordered = models.BooleanField(default=False)
    date_ordered = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0), name="positive_quantity"
            )
        ]

    def __str__(self):
        size_info = f" (taille: {self.size})" if self.size else ""
        return (
            f"{self.quantity} × {self.product.name}{size_info} - {self.user.username}"
        )

    @property
    def total_price(self):
        """Calcule le prix total pour cette commande"""
        return self.quantity * self.product.price

    @property
    def formatted_total(self):
        """Retourne le total formaté"""
        return f"{self.total_price:.2f} €"


# Panier (Cart)

# - Utilisateur
# - Articles
# - Commandé ou non
# - Date de la commande


class Cart(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    orders = models.ManyToManyField(Order, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Panier de {self.user.username}"

    @property
    def total_items(self):
        """Nombre total d'articles dans le panier"""
        return sum(order.quantity for order in self.orders.filter(ordered=False))

    @property
    def total_price(self):
        """Prix total du panier"""
        return sum(
            order.quantity * order.product.price
            for order in self.orders.filter(ordered=False)
        )

    @property
    def formatted_total(self):
        """Retourne le total formaté"""
        return f"{self.total_price:.2f} €"

    @property
    def is_empty(self):
        """Vérifie si le panier est vide"""
        return not self.orders.filter(ordered=False).exists()

    def clear(self):
        """Vide le panier"""
        for order in self.orders.all():
            if not order.ordered:
                order.delete()
        self.orders.clear()


class Wishlist(models.Model):
    """Modèle pour gérer les listes de souhaits des utilisateurs"""

    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        verbose_name = "Liste de souhaits"
        verbose_name_plural = "Listes de souhaits"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
