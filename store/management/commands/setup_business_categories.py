from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Category


class Command(BaseCommand):
    help = "Configure les catégories avec les nouveaux champs métier"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Réinitialise toutes les catégories avec les nouvelles données",
        )

    def handle(self, *args, **options):
        """Configuration complète des catégories avec logique métier améliorée"""

        categories_config = [
            {
                "name": "Women",
                "slug": "women",
                "description": "Collection femme - Élégance et modernité pour toutes les occasions",
                "is_featured": True,
                "display_order": 1,
                "color_theme": "#e91e63",
                "icon_class": "fas fa-female",
                "meta_description": "Découvrez notre collection femme : robes, tops, pantalons et accessoires tendance",
                "meta_keywords": "vêtements femme, mode féminine, robes, tops, pantalons",
            },
            {
                "name": "Men",
                "slug": "men",
                "description": "Collection homme - Style classique et contemporain",
                "is_featured": True,
                "display_order": 2,
                "color_theme": "#2196f3",
                "icon_class": "fas fa-male",
                "meta_description": "Mode masculine : chemises, pantalons, costumes et accessoires pour homme",
                "meta_keywords": "vêtements homme, mode masculine, chemises, costumes, pantalons",
            },
            {
                "name": "Accessories",
                "slug": "accessories",
                "description": "Accessoires mode - Complétez votre look avec style",
                "is_featured": True,
                "display_order": 3,
                "color_theme": "#ff9800",
                "icon_class": "fas fa-gem",
                "meta_description": "Sacs, bijoux, ceintures et accessoires de mode pour homme et femme",
                "meta_keywords": "accessoires mode, sacs, bijoux, ceintures, montres",
            },
            {
                "name": "Sale",
                "slug": "sale",
                "description": "Promotions et soldes - Jusqu'à 70% de réduction",
                "is_featured": True,
                "display_order": 4,
                "color_theme": "#f44336",
                "icon_class": "fas fa-tags",
                "meta_description": "Soldes et promotions mode : réductions jusqu'à 70% sur une sélection",
                "meta_keywords": "soldes, promotions, réductions, vêtements pas cher",
            },
            {
                "name": "New Arrivals",
                "slug": "new-arrivals",
                "description": "Nouveautés - Les dernières tendances mode",
                "is_featured": True,
                "display_order": 5,
                "color_theme": "#4caf50",
                "icon_class": "fas fa-star",
                "meta_description": "Nouveautés mode : découvrez les dernières tendances et nouveaux arrivages",
                "meta_keywords": "nouveautés mode, nouvelles collections, tendances",
            },
            {
                "name": "Kids",
                "slug": "kids",
                "description": "Collection enfant - Mode ludique et confortable",
                "is_featured": True,
                "display_order": 6,
                "color_theme": "#9c27b0",
                "icon_class": "fas fa-child",
                "meta_description": "Vêtements enfant : mode ludique et confortable pour filles et garçons",
                "meta_keywords": "vêtements enfant, mode enfant, vêtements bébé",
            },
            {
                "name": "Shoes",
                "slug": "shoes",
                "description": "Chaussures - Baskets, bottes, escarpins pour tous les styles",
                "is_featured": False,
                "display_order": 7,
                "color_theme": "#795548",
                "icon_class": "fas fa-shoe-prints",
                "meta_description": "Chaussures pour homme et femme : baskets, boots, escarpins, sandales",
                "meta_keywords": "chaussures, baskets, bottes, escarpins, sandales",
            },
            {
                "name": "Bags",
                "slug": "bags",
                "description": "Maroquinerie - Sacs à main, sacs à dos et bagagerie",
                "is_featured": False,
                "display_order": 8,
                "color_theme": "#607d8b",
                "icon_class": "fas fa-shopping-bag",
                "meta_description": "Sacs et maroquinerie : sacs à main, sacs à dos, bagagerie de qualité",
                "meta_keywords": "sacs, maroquinerie, sacs à main, sacs à dos, bagagerie",
            },
            {
                "name": "Jewelry",
                "slug": "jewelry",
                "description": "Bijoux et montres - Pièces élégantes pour sublimer vos tenues",
                "is_featured": False,
                "display_order": 9,
                "color_theme": "#ffc107",
                "icon_class": "fas fa-ring",
                "meta_description": "Bijoux et montres : colliers, bracelets, bagues et montres tendance",
                "meta_keywords": "bijoux, montres, colliers, bracelets, bagues",
            },
            {
                "name": "Sport",
                "slug": "sport",
                "description": "Vêtements de sport - Tenues techniques pour vos activités",
                "is_featured": False,
                "display_order": 10,
                "color_theme": "#00bcd4",
                "icon_class": "fas fa-running",
                "meta_description": "Vêtements de sport : tenues techniques et confortables pour le fitness",
                "meta_keywords": "vêtements sport, fitness, running, yoga, musculation",
            },
        ]

        reset_mode = options.get("reset", False)
        created_count = 0
        updated_count = 0

        self.stdout.write(
            self.style.SUCCESS("=== CONFIGURATION DES CATÉGORIES MÉTIER ===\n")
        )

        for category_data in categories_config:
            try:
                if reset_mode:
                    # Mode reset : supprimer et recréer
                    Category.objects.filter(slug=category_data["slug"]).delete()
                    category = Category.objects.create(**category_data)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Catégorie "{category.name}" recréée avec succès'
                        )
                    )
                else:
                    # Mode normal : get_or_create avec mise à jour
                    category, created = Category.objects.get_or_create(
                        slug=category_data["slug"], defaults=category_data
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Catégorie "{category.name}" créée')
                        )
                    else:
                        # Mettre à jour tous les champs
                        updated = False
                        for field, value in category_data.items():
                            if field != "slug" and getattr(category, field) != value:
                                setattr(category, field, value)
                                updated = True

                        if updated:
                            category.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'↻ Catégorie "{category.name}" mise à jour'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.HTTP_INFO(
                                    f'- Catégorie "{category.name}" déjà à jour'
                                )
                            )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Erreur pour "{category_data["name"]}" : {str(e)}'
                    )
                )

        # Résumé final
        self.stdout.write(self.style.SUCCESS("\n=== RÉSUMÉ ==="))
        self.stdout.write(f"Mode: {'Reset complet' if reset_mode else 'Mise à jour'}")
        self.stdout.write(f"Catégories créées: {created_count}")
        self.stdout.write(f"Catégories mises à jour: {updated_count}")
        self.stdout.write(f"Total des catégories: {Category.objects.count()}")

        # Afficher les catégories vedettes
        self.stdout.write(self.style.SUCCESS("\n=== CATÉGORIES VEDETTES ==="))
        featured_categories = Category.objects.filter(
            is_featured=True, is_active=True
        ).order_by("display_order")

        for category in featured_categories:
            self.stdout.write(
                f"• {category.name} (ordre: {category.display_order}) "
                f"- {category.color_theme} - /{category.slug}/"
            )

        # Statistiques finales
        self.stdout.write(self.style.SUCCESS("\n=== STATISTIQUES ==="))
        total_categories = Category.objects.count()
        active_categories = Category.objects.filter(is_active=True).count()
        featured_categories_count = Category.objects.filter(
            is_featured=True, is_active=True
        ).count()

        self.stdout.write(f"Total: {total_categories}")
        self.stdout.write(f"Actives: {active_categories}")
        self.stdout.write(f"Vedettes: {featured_categories_count}")

        if featured_categories_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Aucune catégorie vedette ! La landing page sera vide."
                )
            )
        elif featured_categories_count > 6:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {featured_categories_count} catégories vedettes "
                    f"(recommandé: 6 max pour l'affichage)"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Configuration terminée ! "
                "Vous pouvez maintenant tester la landing page améliorée."
            )
        )
