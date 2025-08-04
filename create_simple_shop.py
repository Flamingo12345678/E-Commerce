#!/usr/bin/env python
"""
Script simplifié pour créer les données essentielles de votre boutique
"""
import os
import sys
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

import django
django.setup()

from django.db import transaction
from django.contrib.auth.hashers import make_password
from store.models import Category, Product, ProductVariant
from accounts.models import Shopper

def create_shop_essentials():
    """Crée les données essentielles de votre boutique"""

    print("🛍️  CRÉATION DES DONNÉES ESSENTIELLES DE LA BOUTIQUE")
    print("=" * 60)

    try:
        with transaction.atomic():
            print("\n👤 1. Vérification de l'utilisateur...")

            # Vérifier ou créer l'utilisateur flamingo
            shopper, created = Shopper.objects.get_or_create(
                username='flamingo',
                defaults={
                    'email': 'ernestyombi20@gmail.com',
                    'first_name': 'Ernest',
                    'last_name': 'Évrard Yombi',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                    'password': make_password('admin123'),  # Mot de passe simple pour test
                }
            )

            if created:
                print(f"✅ Utilisateur créé: {shopper.username}")
            else:
                print(f"✅ Utilisateur existant: {shopper.username}")

            print("\n📂 2. Création des catégories...")

            # Supprimer les catégories existantes pour recommencer proprement
            Category.objects.all().delete()

            categories_data = [
                {'name': 'Women', 'slug': 'women', 'description': 'Collection femme élégante', 'display_order': 1},
                {'name': 'Men', 'slug': 'men', 'description': 'Collection homme moderne', 'display_order': 2},
                {'name': 'Accessories', 'slug': 'accessories', 'description': 'Accessoires de mode', 'display_order': 3},
                {'name': 'Chaussures', 'slug': 'chaussures', 'description': 'Chaussures pour tous styles', 'display_order': 4},
                {'name': 'Enfants', 'slug': 'enfants', 'description': 'Mode enfantine', 'display_order': 5}
            ]

            created_categories = {}
            for cat_data in categories_data:
                category = Category.objects.create(**cat_data)
                created_categories[cat_data['slug']] = category
                print(f"✅ Catégorie créée: {category.name}")

            print("\n👕 3. Création des produits...")

            # Supprimer les produits existants
            Product.objects.all().delete()

            # Créer les produits principaux de votre boutique
            products_data = [
                {
                    'name': 'Vogue T-Shirt Black Homme',
                    'slug': 'vogue-tshirt-black-homme',
                    'price': Decimal('39.99'),
                    'description': 'T-shirt Vogue pour homme, chic et intemporel.',
                    'category': created_categories['men'],
                    'variants': [
                        {'size': 'XS', 'stock': 30},
                        {'size': 'S', 'stock': 30},
                        {'size': 'M', 'stock': 30},
                        {'size': 'L', 'stock': 28},  # Quelques vendus
                        {'size': 'XL', 'stock': 29}  # Quelques vendus
                    ]
                },
                {
                    'name': 'Vogue T-Shirt Black Femme',
                    'slug': 'vogue-tshirt-black-femme',
                    'price': Decimal('49.99'),
                    'description': 'T-shirt Vogue pour femme, chic et intemporel.',
                    'category': created_categories['women'],
                    'variants': [
                        {'size': 'XS', 'stock': 30},
                        {'size': 'S', 'stock': 30},
                        {'size': 'M', 'stock': 30},
                        {'size': 'L', 'stock': 30},
                        {'size': 'XL', 'stock': 30}
                    ]
                },
                {
                    'name': 'Vêtement Orange',
                    'slug': 'vetement-orange',
                    'price': Decimal('42.50'),
                    'description': 'Vêtement féminin moderne et coloré.',
                    'category': created_categories['women'],
                    'shoe_size': Decimal('5.0'),
                    'variants': [
                        {'size': 'XS', 'stock': 30},
                        {'size': 'S', 'stock': 30},
                        {'size': 'M', 'stock': 30},
                        {'size': 'L', 'stock': 30},
                        {'size': 'XL', 'stock': 30}
                    ]
                },
                {
                    'name': 'Chaussures Élégantes',
                    'slug': 'chaussures-elegantes',
                    'price': Decimal('58.75'),
                    'description': 'Chaussures élégantes pour toutes occasions.',
                    'category': created_categories['chaussures'],
                    'variants': [
                        {'size': '39', 'stock': 30},
                        {'size': '40', 'stock': 30},
                        {'size': '41', 'stock': 30},
                        {'size': '42', 'stock': 30},
                        {'size': '43', 'stock': 30},
                        {'size': '44', 'stock': 30}
                    ]
                }
            ]

            total_variants = 0
            for prod_data in products_data:
                variants_data = prod_data.pop('variants')

                product = Product.objects.create(**prod_data)
                print(f"✅ Produit créé: {product.name} - {product.price}€")

                # Créer les variantes
                for variant_data in variants_data:
                    ProductVariant.objects.create(
                        product=product,
                        size=variant_data['size'],
                        stock=variant_data['stock'],
                        price=product.price
                    )
                    total_variants += 1

                print(f"   📦 {len(variants_data)} variantes créées")

            print("\n🎉 CRÉATION TERMINÉE AVEC SUCCÈS!")
            print("=" * 60)
            print(f"✅ Utilisateur: {shopper.username}")
            print(f"✅ Catégories: {len(categories_data)}")
            print(f"✅ Produits: {len(products_data)}")
            print(f"✅ Variantes: {total_variants}")

            return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_shop_essentials()

    if success:
        print(f"\n🚀 BOUTIQUE CRÉÉE AVEC SUCCÈS!")
        print("📱 Prochaines étapes:")
        print("   1. python manage.py runserver")
        print("   2. Aller sur http://localhost:8000/")
        print("   3. Admin: http://localhost:8000/admin/")
        print("   4. Login: flamingo / admin123")
    else:
        print(f"\n❌ Échec de la création")
        sys.exit(1)
