from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Category


class Command(BaseCommand):
    help = "Crée les catégories de base pour la boutique fashion"

    def handle(self, *args, **options):
        categories_data = [
            {
                "name": "Women",
                "slug": "women",
                "description": "Collection femme - Vêtements élégants et contemporains pour toutes les occasions.",
            },
            {
                "name": "Men",
                "slug": "men",
                "description": "Collection homme - Style classique et moderne pour l'homme d'aujourd'hui.",
            },
            {
                "name": "Accessories",
                "slug": "accessories",
                "description": "Accessoires de mode - Complétez votre look avec nos sacs, bijoux et accessoires.",
            },
            {
                "name": "Sale",
                "slug": "sale",
                "description": "Promotions et soldes - Jusqu'à 70% de réduction sur une sélection d'articles.",
            },
            {
                "name": "New Arrivals",
                "slug": "new-arrivals",
                "description": "Nouveautés - Découvrez les dernières tendances et nouveaux arrivages.",
            },
            {
                "name": "Kids",
                "slug": "kids",
                "description": "Collection enfant - Vêtements confortables et stylés pour les plus jeunes.",
            },
            {
                "name": "Shoes",
                "slug": "shoes",
                "description": "Chaussures pour tous - Baskets, bottes, escarpins et plus encore.",
            },
            {
                "name": "Bags",
                "slug": "bags",
                "description": "Maroquinerie - Sacs à main, sacs à dos et bagagerie de qualité.",
            },
            {
                "name": "Jewelry",
                "slug": "jewelry",
                "description": "Bijoux et montres - Pièces élégantes pour sublimer vos tenues.",
            },
            {
                "name": "Sport",
                "slug": "sport",
                "description": "Vêtements de sport - Tenues techniques et confortables pour vos activités.",
            },
        ]

        created_count = 0
        updated_count = 0

        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=category_data["slug"],
                defaults={
                    "name": category_data["name"],
                    "description": category_data["description"],
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Catégorie "{category.name}" créée avec succès'
                    )
                )
            else:
                # Mettre à jour la description si elle a changé
                if category.description != category_data["description"]:
                    category.description = category_data["description"]
                    category.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Catégorie "{category.name}" mise à jour')
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f'- Catégorie "{category.name}" existe déjà'
                        )
                    )

        # Résumé final
        self.stdout.write(self.style.SUCCESS("\n=== RÉSUMÉ ==="))
        self.stdout.write(f"Catégories créées: {created_count}")
        self.stdout.write(f"Catégories mises à jour: {updated_count}")
        self.stdout.write(f"Total des catégories: {Category.objects.count()}")

        # Afficher toutes les catégories
        self.stdout.write(self.style.SUCCESS("\n=== CATÉGORIES DISPONIBLES ==="))
        for category in Category.objects.all().order_by("name"):
            self.stdout.write(f"• {category.name} (/{category.slug}/)")
