#!/usr/bin/env python
"""
Script pour créer TOUS les produits originaux de votre boutique (34 produits)
"""
import os
import sys
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

import django
django.setup()

from django.db import transaction
from store.models import Category, Product, ProductVariant

def create_all_original_products():
    """Crée tous les 34 produits originaux de votre boutique"""

    print("🛍️  RÉCUPÉRATION DE TOUS VOS PRODUITS ORIGINAUX")
    print("=" * 60)

    try:
        with transaction.atomic():
            # Récupérer les catégories existantes
            categories = {
                1: Category.objects.get(slug='women'),     # Women
                2: Category.objects.get(slug='men'),       # Men
                3: Category.objects.get(slug='accessories'), # Accessories
                4: Category.objects.get(slug='chaussures'), # Chaussures (était 'chaussure' dans vos données)
            }

            print(f"✅ Catégories trouvées: {len(categories)}")

            # Supprimer les produits existants pour recommencer
            Product.objects.all().delete()
            print("🗑️  Anciens produits supprimés")

            # TOUS vos 34 produits originaux extraits de votre sauvegarde SQL
            all_products = [
                # Produit 1
                {'name': 'Aiony Haust Ixyxqp4Zejo Unsplash', 'slug': 'aiony-haust-ixyxqp4zejo-unsplash', 'price': Decimal('57.02'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/aiony-haust-IXYxqP4zejo-unsplash.jpg', 'category': categories[1]},

                # Produit 2
                {'name': 'Alexi Romano Ccx6Fz Cmoi Unsplash', 'slug': 'alexi-romano-ccx6fz-cmoi-unsplash', 'price': Decimal('40.06'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/alexi-romano-CCx6Fz_CmOI-unsplash.jpg', 'category': categories[1]},

                # Produit 3
                {'name': 'Anton Van Der Weijst Th Byj Iwbo Unsplash', 'slug': 'anton-van-der-weijst-th-byj-iwbo-unsplash', 'price': Decimal('32.62'), 'description': 'Look masculin affirmé, parfait pour un style urbain et décontracté.', 'thumbnail': 'products/anton-van-der-weijst-tH_Byj_IWbo-unsplash.jpg', 'category': categories[2]},

                # Produit 4
                {'name': 'Atikh Bana Kamtemjnxy Unsplash', 'slug': 'atikh-bana-kamtemjnxy-unsplash', 'price': Decimal('53.97'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/atikh-bana-_KaMTEmJnxY-unsplash.jpg', 'category': categories[2]},

                # Produit 5
                {'name': 'C1001 51 2 Y2Ufdqw', 'slug': 'c1001-51-2-y2ufdqw', 'price': Decimal('53.74'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/C1001-51-2_Y2UFDqw.webp', 'category': categories[4]},

                # Produit 6
                {'name': 'C1001 51 2', 'slug': 'c1001-51-2', 'price': Decimal('58.75'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/C1001-51-2.webp', 'category': categories[4]},

                # Produit 7
                {'name': 'Cesar La Rosa Hbaddptme1Q Unsplash', 'slug': 'cesar-la-rosa-hbaddptme1q-unsplash', 'price': Decimal('53.84'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/cesar-la-rosa-HbAddptme1Q-unsplash.jpg', 'category': categories[2]},

                # Produit 8
                {'name': 'Dami Adebayo K6Aqzmibr1S Unsplash', 'slug': 'dami-adebayo-k6aqzmibr1s-unsplash', 'price': Decimal('35.62'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/dami-adebayo-k6aQzmIbR1s-unsplash.jpg', 'category': categories[2]},

                # Produit 9
                {'name': 'Dane Wetton Tl80Dknqe5A Unsplash', 'slug': 'dane-wetton-tl80dknqe5a-unsplash', 'price': Decimal('52.25'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/dane-wetton-Tl80dkNQE5A-unsplash.jpg', 'category': categories[2]},

                # Produit 10
                {'name': 'Dom Hill Nimeltctnyy Unsplash', 'slug': 'dom-hill-nimeltctnyy-unsplash', 'price': Decimal('41.35'), 'description': 'Look masculin affirmé, parfait pour un style urbain et décontracté.', 'thumbnail': 'products/dom-hill-nimElTcTNyY-unsplash.jpg', 'category': categories[2]},

                # Produit 11
                {'name': 'Farol 106 Jlriatalava Unsplash', 'slug': 'farol-106-jlriatalava-unsplash', 'price': Decimal('46.21'), 'description': 'Sac ou accessoire tendance pour compléter votre look avec élégance.', 'thumbnail': 'products/farol-106-JlriaTaLavA-unsplash.jpg', 'category': categories[3]},

                # Produit 12
                {'name': 'Influence Blonde Posant', 'slug': 'influence-blonde-posant', 'price': Decimal('38.41'), 'description': 'Vêtement féminin moderne, idéal pour sublimer votre garde-robe.', 'thumbnail': 'products/influence-blonde-posant.jpg', 'category': categories[1]},

                # Produit 13
                {'name': 'Iurii Melentsov 7Ikub62Cqbu Unsplash', 'slug': 'iurii-melentsov-7ikub62cqbu-unsplash', 'price': Decimal('40.99'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/iurii-melentsov-7iKuB62CQBU-unsplash.jpg', 'category': categories[2]},

                # Produit 14
                {'name': 'Judeus Samson 0Ueccinucr4 Unsplash', 'slug': 'judeus-samson-0ueccinucr4-unsplash', 'price': Decimal('37.93'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/judeus-samson-0UECcInuCR4-unsplash.jpg', 'category': categories[2]},

                # Produit 15
                {'name': 'Kevin Laminto Hjakd8O2Rmg Unsplash', 'slug': 'kevin-laminto-hjakd8o2rmg-unsplash', 'price': Decimal('41.79'), 'description': 'Look masculin affirmé, parfait pour un style urbain et décontracté.', 'thumbnail': 'products/kevin-laminto-hjAkD8o2rmg-unsplash.jpg', 'category': categories[2]},

                # Produit 16
                {'name': 'Kristina Petrick Qmyebfkk3Pw Unsplash', 'slug': 'kristina-petrick-qmyebfkk3pw-unsplash', 'price': Decimal('43.38'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/kristina-petrick-qmyebfKk3pw-unsplash.jpg', 'category': categories[1]},

                # Produit 17
                {'name': 'Mohamadreza Khashay Xwmyvkn14Ok Unsplash', 'slug': 'mohamadreza-khashay-xwmyvkn14ok-unsplash', 'price': Decimal('30.15'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/mohamadreza-khashay-xwMYVKN14Ok-unsplash.jpg', 'category': categories[2]},

                # Produit 18
                {'name': 'Mohamadreza Khashay Ziubudophmc Unsplash', 'slug': 'mohamadreza-khashay-ziubudophmc-unsplash', 'price': Decimal('39.02'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/mohamadreza-khashay-ziubUDopHmc-unsplash.jpg', 'category': categories[2]},

                # Produit 19
                {'name': 'Molly Mears 4 90Zmmdo 4 Unsplash', 'slug': 'molly-mears-4-90zmmdo-4-unsplash', 'price': Decimal('46.59'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/molly-mears-4_90zmmdo_4-unsplash.jpg', 'category': categories[1]},

                # Produit 20
                {'name': 'Naeim Jafari 6Xai7Xxogbc Unsplash', 'slug': 'naeim-jafari-6xai7xxogbc-unsplash', 'price': Decimal('57.02'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/naeim-jafari-6Xai7XxOgBc-unsplash.jpg', 'category': categories[2]},

                # Produit 21
                {'name': 'Nick Karvounis U6A6Zc3P8Tm Unsplash', 'slug': 'nick-karvounis-u6a6zc3p8tm-unsplash', 'price': Decimal('38.73'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/nick-karvounis-U6a6zC3P8tM-unsplash.jpg', 'category': categories[2]},

                # Produit 22
                {'name': 'Oladimeji Odunsi Wu3Yqve2Gnc Unsplash', 'slug': 'oladimeji-odunsi-wu3yqve2gnc-unsplash', 'price': Decimal('54.35'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/oladimeji-odunsi-Wu3yqve2gnc-unsplash.jpg', 'category': categories[2]},

                # Produit 23
                {'name': 'Ospan Ali Nyrssbzhz4Y Unsplash', 'slug': 'ospan-ali-nyrssbzhz4y-unsplash', 'price': Decimal('57.09'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/ospan-ali-nyrSsBzhZ4Y-unsplash.jpg', 'category': categories[2]},

                # Produit 24
                {'name': 'Philipp Arlt Nmh9A0Obon8 Unsplash', 'slug': 'philipp-arlt-nmh9a0obon8-unsplash', 'price': Decimal('56.94'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/philipp-arlt-NmH9A0obon8-unsplash.jpg', 'category': categories[2]},

                # Produit 25
                {'name': 'Reza Delkhosh Iraojytphze Unsplash', 'slug': 'reza-delkhosh-iraojytphze-unsplash', 'price': Decimal('30.09'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/reza-delkhosh-iRAOJYtPHZE-unsplash.jpg', 'category': categories[2]},

                # Produit 26
                {'name': 'Sara Dabaghian Zain5Wnsr0E Unsplash', 'slug': 'sara-dabaghian-zain5wnsr0e-unsplash', 'price': Decimal('31.07'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/sara-dabaghian-ZAiN5wnsR0E-unsplash.jpg', 'category': categories[1]},

                # Produit 27
                {'name': 'Sirio 7 Znlvljchs Unsplash', 'slug': 'sirio-7-znlvljchs-unsplash', 'price': Decimal('37.27'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/sirio-7_ZNLVlJchs-unsplash.jpg', 'category': categories[2]},

                # Produit 28
                {'name': 'Tamara Bellis Grfla7Axlo4 Unsplash', 'slug': 'tamara-bellis-grfla7axlo4-unsplash', 'price': Decimal('45.36'), 'description': 'Découvrez notre collection femme : élégance et modernité au rendez-vous.', 'thumbnail': 'products/tamara-bellis-GRfLA7aXlO4-unsplash.jpg', 'category': categories[1]},

                # Produit 29
                {'name': 'Vetement Orange Olmuzcr', 'slug': 'vetement-orange-olmuzcr', 'price': Decimal('39.70'), 'description': 'Vêtement féminin moderne, idéal pour sublimer votre garde-robe.', 'thumbnail': 'products/Vetement-orange_olMuzCr.jpg', 'category': categories[2]},

                # Produit 30
                {'name': 'Vetement Orange', 'slug': 'vetement-orange', 'price': Decimal('42.50'), 'description': 'Vêtement féminin moderne, idéal pour sublimer votre garde-robe.', 'thumbnail': 'products/Vetement-orange.jpg', 'shoe_size': Decimal('5.0'), 'category': categories[1]},

                # Produit 31
                {'name': 'Vladimir Yelizarov Tgrks1Cv Ha Unsplash', 'slug': 'vladimir-yelizarov-tgrks1cv-ha-unsplash', 'price': Decimal('45.99'), 'description': 'Collection homme : des vêtements pensés pour le confort et le style.', 'thumbnail': 'products/vladimir-yelizarov-tGRks1CV_HA-unsplash.jpg', 'shoe_size': Decimal('5.0'), 'category': categories[1]},

                # Produit 32
                {'name': 'Vogue T Shirt Black', 'slug': 'vogue-t-shirt-black', 'price': Decimal('49.99'), 'description': 'T-shirt Vogue pour femme, chic et intemporel.', 'thumbnail': 'products/Vogue_T-Shirt_black_2_CKtj4WL.webp', 'shoe_size': Decimal('5.0'), 'category': categories[1]},

                # Produit 33
                {'name': 'Vogue T-Shirt Black Homme', 'slug': 'vogue-t-shirt-black-2', 'price': Decimal('39.99'), 'description': 'T-shirt Vogue pour homme, chic et intemporel.', 'thumbnail': 'products/Vogue_T-Shirt_black_2.webp', 'category': categories[2]},

                # Produit 34
                {'name': 'Vogue T Shirt Black 2 Cktj4Wl', 'slug': 'vogue-t-shirt-black-2-cktj4wl', 'price': Decimal('49.51'), 'description': 'T-shirt Vogue pour femme, chic et intemporel.', 'thumbnail': 'products/Vogue_T-Shirt_black_2_CKtj4WL.webp', 'category': categories[1]}
            ]

            print(f"\n📦 Création de {len(all_products)} produits...")

            total_variants = 0
            for i, product_data in enumerate(all_products, 1):
                product = Product.objects.create(**product_data)
                print(f"✅ {i:2d}/34 - {product.name[:50]}... - {product.price}€")

                # Créer des variantes standard pour chaque produit
                if product.category.slug in ['women', 'men']:
                    # Vêtements : tailles XS à XL
                    sizes = ['XS', 'S', 'M', 'L', 'XL']
                elif product.category.slug == 'chaussures':
                    # Chaussures : pointures 39 à 46
                    sizes = ['39', '40', '41', '42', '43', '44', '45', '46']
                else:
                    # Accessoires : tailles universelles
                    sizes = ['M', 'L']

                for size in sizes:
                    ProductVariant.objects.create(
                        product=product,
                        size=size,
                        stock=30,  # Stock standard
                        price=product.price
                    )
                    total_variants += 1

            print(f"\n🎉 CRÉATION TERMINÉE AVEC SUCCÈS!")
            print("=" * 60)
            print(f"✅ Produits créés: {len(all_products)}")
            print(f"✅ Variantes créées: {total_variants}")
            print(f"✅ Catégories utilisées: {len(categories)}")

            # Statistiques par catégorie
            print(f"\n📊 RÉPARTITION PAR CATÉGORIE:")
            for cat_id, category in categories.items():
                count = sum(1 for p in all_products if p['category'] == category)
                print(f"   {category.name}: {count} produits")

            return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_all_original_products()

    if success:
        print(f"\n🚀 CATALOGUE COMPLET RESTAURÉ!")
        print("📱 Votre boutique contient maintenant:")
        print("   • 34 produits originaux")
        print("   • Toutes les variantes de tailles")
        print("   • Prix et descriptions originaux")
        print("   • Images originales")
        print("\n🔗 Testez maintenant:")
        print("   1. python manage.py runserver")
        print("   2. http://localhost:8000/")
    else:
        print(f"\n❌ Échec de la restauration")
        sys.exit(1)
