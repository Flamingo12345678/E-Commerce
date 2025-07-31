from django.core.management.base import BaseCommand
from store.models import Product, Category, ProductVariant
from django.utils.text import slugify
import os
import random

# Tableau de correspondance image/catégorie validé
PRODUCTS = [
    ("aiony-haust-IXYxqP4zejo-unsplash.jpg", "Women"),
    ("alexi-romano-CCx6Fz_CmOI-unsplash.jpg", "Women"),
    ("anton-van-der-weijst-tH_Byj_IWbo-unsplash.jpg", "Men"),
    ("atikh-bana-_KaMTEmJnxY-unsplash.jpg", "Men"),
    ("C1001-51-2_Y2UFDqw.webp", "Women"),
    ("C1001-51-2.webp", "Women"),
    ("cesar-la-rosa-HbAddptme1Q-unsplash.jpg", "Men"),
    ("dami-adebayo-k6aQzmIbR1s-unsplash.jpg", "Men"),
    ("dane-wetton-Tl80dkNQE5A-unsplash.jpg", "Men"),
    ("dom-hill-nimElTcTNyY-unsplash.jpg", "Men"),
    ("farol-106-JlriaTaLavA-unsplash.jpg", "Accessories"),
    ("influence-blonde-posant.jpg", "Women"),
    ("iurii-melentsov-7iKuB62CQBU-unsplash.jpg", "Men"),
    ("judeus-samson-0UECcInuCR4-unsplash.jpg", "Men"),
    ("kevin-laminto-hjAkD8o2rmg-unsplash.jpg", "Men"),
    ("kristina-petrick-qmyebfKk3pw-unsplash.jpg", "Women"),
    ("mohamadreza-khashay-xwMYVKN14Ok-unsplash.jpg", "Men"),
    ("mohamadreza-khashay-ziubUDopHmc-unsplash.jpg", "Men"),
    ("molly-mears-4_90zmmdo_4-unsplash.jpg", "Women"),
    ("naeim-jafari-6Xai7XxOgBc-unsplash.jpg", "Men"),
    ("nick-karvounis-U6a6zC3P8tM-unsplash.jpg", "Men"),
    ("oladimeji-odunsi-Wu3yqve2gnc-unsplash.jpg", "Men"),
    ("ospan-ali-nyrSsBzhZ4Y-unsplash.jpg", "Men"),
    ("philipp-arlt-NmH9A0obon8-unsplash.jpg", "Men"),
    ("reza-delkhosh-iRAOJYtPHZE-unsplash.jpg", "Men"),
    ("sara-dabaghian-ZAiN5wnsR0E-unsplash.jpg", "Women"),
    ("sirio-7_ZNLVlJchs-unsplash.jpg", "Men"),
    ("tamara-bellis-GRfLA7aXlO4-unsplash.jpg", "Women"),
    ("Vetement-orange_olMuzCr.jpg", "Women"),
    ("Vetement-orange.jpg", "Women"),
    ("vladimir-yelizarov-tGRks1CV_HA-unsplash.jpg", "Men"),
    ("Vogue_T-Shirt_black_2_CKtj4WL.webp", "Women"),
    ("Vogue_T-Shirt_black_2.webp", "Women"),
]

class Command(BaseCommand):
    help = "Importe les produits à partir des images et les classe dans la bonne catégorie."

    def get_description(self, name, cat_name):
        """Retourne une description personnalisée selon le produit et la catégorie."""
        name_lower = name.lower()
        if cat_name == "Women":
            if "t-shirt" in name_lower:
                return "T-shirt tendance pour femme, confortable et stylé. Parfait pour toutes les occasions."
            if "vetement" in name_lower or "influence" in name_lower:
                return "Vêtement féminin moderne, idéal pour sublimer votre garde-robe."
            if "vogue" in name_lower:
                return "T-shirt Vogue pour femme, chic et intemporel."
            return "Découvrez notre collection femme : élégance et modernité au rendez-vous."
        if cat_name == "Men":
            if "t-shirt" in name_lower:
                return "T-shirt classique pour homme, coupe moderne et tissu de qualité."
            if "anton" in name_lower or "dom" in name_lower or "kevin" in name_lower:
                return "Look masculin affirmé, parfait pour un style urbain et décontracté."
            return "Collection homme : des vêtements pensés pour le confort et le style."
        if cat_name == "Accessories":
            if "farol" in name_lower:
                return "Sac ou accessoire tendance pour compléter votre look avec élégance."
            return "Accessoire de mode indispensable pour sublimer votre tenue."
        return f"Produit automatique pour {cat_name} : qualité et style au rendez-vous."

    def create_categories_if_needed(self):
        """Crée les catégories nécessaires si elles n'existent pas."""
        categories = [
            ("Women", "Collection femme - Vêtements élégants et contemporains pour toutes les occasions."),
            ("Men", "Collection homme - Style classique et moderne pour l'homme d'aujourd'hui."),
            ("Accessories", "Accessoires de mode - Complétez votre look avec nos sacs, bijoux et accessoires."),
        ]
        for name, description in categories:
            obj, created = Category.objects.get_or_create(name=name, defaults={
                "slug": slugify(name),
                "description": description
            })
            if created:
                self.stdout.write(self.style.SUCCESS(f"Catégorie '{name}' créée."))

    def create_variants(self, product, cat_name, name):
        """Crée les variantes de taille et stock pour le produit selon la catégorie ou le type."""
        import random
        variants = []
        if cat_name in ["Women", "Men"]:
            sizes = ["S", "M", "L", "XL"]
            for size in sizes:
                stock = random.randint(5, 20)
                variants.append(ProductVariant(product=product, size=size, stock=stock, price=product.price))
        elif cat_name == "Accessories":
            variants.append(ProductVariant(product=product, size="TU", stock=random.randint(10, 30), price=product.price))
        elif "c1001" in name.lower():  # Chaussures
            sizes = ["38", "39", "40", "41", "42"]
            for size in sizes:
                stock = random.randint(3, 10)
                variants.append(ProductVariant(product=product, size=size, stock=stock, price=product.price))
        if variants:
            ProductVariant.objects.bulk_create(variants)

    def add_variants_to_existing_products(self):
        """Ajoute les variantes XS, S, M, L, XL (stock 30) à tous les produits sauf chaussures et accessoires.
        Pour les chaussures (C1001 dans le nom), ajoute les tailles 39 à 46 (stock 30).
        """
        sizes_clothes = ["XS", "S", "M", "L", "XL"]
        sizes_shoes = ["39", "40", "41", "42", "43", "44", "45", "46"]
        for product in Product.objects.all():
            name_lower = product.name.lower()
            # Accessoires : ignorer
            if product.category and product.category.name == "Accessories":
                continue
            # Chaussures (C1001 dans le nom)
            if "c1001" in name_lower:
                for size in sizes_shoes:
                    if not ProductVariant.objects.filter(product=product, size=size).exists():
                        ProductVariant.objects.create(
                            product=product,
                            size=size,
                            stock=30,
                            price=product.price
                        )
                continue
            # Autres produits (vêtements)
            for size in sizes_clothes:
                if not ProductVariant.objects.filter(product=product, size=size).exists():
                    ProductVariant.objects.create(
                        product=product,
                        size=size,
                        stock=30,
                        price=product.price
                    )

    def handle(self, *args, **options):
        self.create_categories_if_needed()
        base_path = "products/"  # relatif à MEDIA_ROOT
        for filename, cat_name in PRODUCTS:
            # Cherche la catégorie
            try:
                category = Category.objects.get(name__iexact=cat_name)
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Catégorie '{cat_name}' non trouvée."))
                continue
            name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
            slug = slugify(name)
            # Prix aléatoire entre 29.99 et 59.99
            price = round(random.uniform(29.99, 59.99), 2)
            # Description personnalisée
            description = self.get_description(name, cat_name)
            # Vérifie si le produit existe déjà
            if Product.objects.filter(slug=slug).exists():
                self.stdout.write(self.style.WARNING(f"Produit '{name}' déjà existant, ignoré."))
                continue
            product = Product.objects.create(
                name=name,
                slug=slug,
                price=price,
                description=description,
                thumbnail=base_path + filename,
                category=category,
            )
            self.create_variants(product, cat_name, name)
            self.stdout.write(self.style.SUCCESS(f"Produit '{name}' ajouté à la catégorie '{cat_name}' avec le prix {price}€. Description : {description}"))
        self.add_variants_to_existing_products()
