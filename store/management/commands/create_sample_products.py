from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Product, Category
import random


class Command(BaseCommand):
    help = "Créé des produits de test pour la landing page"

    def handle(self, *args, **options):
        # Créer quelques produits de test
        products_data = [
            {
                "name": "Produit Performance 6",
                "price": 12.00,
                "stock": 19,
                "description": "Un produit de qualité premium avec des finitions exceptionnelles.",
                "rating": 3.0,
                "review_count": 5,
                "category": "women",
            },
            {
                "name": "Produit Performance 1",
                "price": 10.00,
                "stock": 20,
                "description": "Un produit polyvalent pour tous les styles.",
                "rating": 4.0,
                "review_count": 23,
                "category": "men",
            },
            {
                "name": "Produit Scénario",
                "price": 30.00,
                "stock": 2,
                "description": "Une pièce unique pour les occasions spéciales.",
                "rating": 5.0,
                "review_count": 23,
                "category": "new-arrivals",
            },
            {
                "name": "Produit Combo Test",
                "price": 25.00,
                "stock": 5,
                "description": "Un combo parfait pour compléter votre garde-robe.",
                "rating": 4.0,
                "review_count": 23,
                "category": "women",
            },
            {
                "name": "Produit Test Panier",
                "price": 20.00,
                "stock": 10,
                "description": "Un produit idéal pour tester nos fonctionnalités.",
                "rating": 4.0,
                "review_count": 23,
                "category": "sale",
            },
            {
                "name": "Blazer Élégant Femme",
                "price": 89.00,
                "stock": 15,
                "description": "Blazer élégant parfait pour le bureau ou les sorties.",
                "rating": 4.5,
                "review_count": 34,
                "category": "women",
            },
            {
                "name": "Jean Homme Classic",
                "price": 45.00,
                "stock": 25,
                "description": "Jean coupe classique, confortable et durable.",
                "rating": 4.2,
                "review_count": 67,
                "category": "men",
            },
            {
                "name": "Sac à Main Cuir",
                "price": 120.00,
                "stock": 8,
                "description": "Sac à main en cuir véritable, élégant et pratique.",
                "rating": 4.8,
                "review_count": 18,
                "category": "accessories",
            },
        ]

        created_count = 0

        for product_data in products_data:
            # Récupérer la catégorie
            try:
                category = Category.objects.get(slug=product_data["category"])
            except Category.DoesNotExist:
                category = None
                self.stdout.write(
                    self.style.WARNING(
                        f'Catégorie "{product_data["category"]}" non trouvée pour {product_data["name"]}'
                    )
                )

            # Créer le slug
            slug = slugify(product_data["name"])

            # Vérifier si le produit existe déjà
            if not Product.objects.filter(slug=slug).exists():
                product = Product.objects.create(
                    name=product_data["name"],
                    slug=slug,
                    price=product_data["price"],
                    stock=product_data["stock"],
                    description=product_data["description"],
                    rating=product_data["rating"],
                    review_count=product_data["review_count"],
                    category=category,
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Produit "{product.name}" créé avec succès')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Produit "{product_data["name"]}" existe déjà'
                    )
                )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"=== RÉSUMÉ ==="))
        self.stdout.write(self.style.SUCCESS(f"Produits créés: {created_count}"))

        total_products = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total des produits: {total_products}"))
        self.stdout.write("=" * 50)
