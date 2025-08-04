#!/usr/bin/env python
"""
Script pour créer manuellement les données essentielles de votre boutique
"""
import os
import sys
from decimal import Decimal
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

import django
django.setup()

from django.db import transaction
from django.contrib.auth.hashers import make_password
from store.models import Category, Product, ProductVariant, Cart, Order
from accounts.models import Shopper, PaymentMethod, Transaction

def create_essential_data():
    """Crée les données essentielles de votre boutique e-commerce"""

    print("🛍️  CRÉATION DES DONNÉES DE VOTRE BOUTIQUE E-COMMERCE")
    print("=" * 60)

    try:
        with transaction.atomic():
            print("\n👤 1. Création de l'utilisateur principal...")

            # Créer l'utilisateur flamingo (s'il n'existe pas déjà)
            shopper, created = Shopper.objects.get_or_create(
                username='flamingo',
                defaults={
                    'email': 'ernestyombi20@gmail.com',
                    'first_name': 'Ernest',
                    'last_name': 'Évrard Yombi',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                    'password': make_password('votre_mot_de_passe_admin'),  # À changer
                    'firebase_uid': 'FY1HywSdcYO7FDsv7PTZsBWaWCT2'
                }
            )

            if created:
                print(f"✅ Utilisateur créé: {shopper.username} ({shopper.email})")
            else:
                print(f"✅ Utilisateur existant: {shopper.username}")

            print("\n📂 2. Création des catégories...")

            # Créer les catégories
            categories_data = [
                {'name': 'Women', 'slug': 'women', 'description': 'Collection femme - Vêtements élégants et contemporains pour toutes les occasions.', 'display_order': 1},
                {'name': 'Men', 'slug': 'men', 'description': 'Collection homme - Style classique et moderne pour l\'homme d\'aujourd\'hui.', 'display_order': 2},
                {'name': 'Accessories', 'slug': 'accessories', 'description': 'Accessoires de mode - Complétez votre look avec nos sacs, bijoux et accessoires.', 'display_order': 3},
                {'name': 'Chaussure', 'slug': 'chaussure', 'description': 'Chaussures de qualité pour tous les styles.', 'display_order': 4},
                {'name': 'Enfants', 'slug': 'enfants', 'description': 'Mode enfantine et colorée.', 'display_order': 5}
            ]

            created_categories = {}
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    slug=cat_data['slug'],
                    defaults=cat_data
                )
                created_categories[cat_data['slug']] = category
                if created:
                    print(f"✅ Catégorie créée: {category.name}")
                else:
                    print(f"✅ Catégorie existante: {category.name}")

            print("\n👕 3. Création des produits phares...")

            # Créer quelques produits phares de votre boutique
            products_data = [
                {
                    'name': 'Vogue T-Shirt Black',
                    'slug': 'vogue-t-shirt-black',
                    'price': Decimal('39.99'),
                    'description': 'T-shirt Vogue pour homme, chic et intemporel.',
                    'thumbnail': 'products/Vogue_T-Shirt_black_2.webp',
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
                    'slug': 'vogue-t-shirt-black-femme',
                    'price': Decimal('49.99'),
                    'description': 'T-shirt Vogue pour femme, chic et intemporel.',
                    'thumbnail': 'products/Vogue_T-Shirt_black_2_CKtj4WL.webp',
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
                    'description': 'Vêtement féminin moderne, idéal pour sublimer votre garde-robe.',
                    'thumbnail': 'products/Vetement-orange.jpg',
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
                    'thumbnail': 'products/C1001-51-2.webp',
                    'category': created_categories['chaussure'],
                    'variants': [
                        {'size': '39', 'stock': 30},
                        {'size': '40', 'stock': 30},
                        {'size': '41', 'stock': 30},
                        {'size': '42', 'stock': 30},
                        {'size': '43', 'stock': 30},
                        {'size': '44', 'stock': 30},
                        {'size': '45', 'stock': 30},
                        {'size': '46', 'stock': 30}
                    ]
                }
            ]

            created_products = []
            for prod_data in products_data:
                variants_data = prod_data.pop('variants')

                product, created = Product.objects.get_or_create(
                    slug=prod_data['slug'],
                    defaults=prod_data
                )
                created_products.append(product)

                if created:
                    print(f"✅ Produit créé: {product.name} - {product.price}€")

                    # Créer les variantes
                    for variant_data in variants_data:
                        ProductVariant.objects.create(
                            product=product,
                            size=variant_data['size'],
                            stock=variant_data['stock'],
                            price=product.price
                        )
                    print(f"   📦 {len(variants_data)} variantes créées")
                else:
                    print(f"✅ Produit existant: {product.name}")

            print("\n💳 4. Création de la méthode de paiement...")

            # Créer la méthode de paiement Stripe
            payment_method, created = PaymentMethod.objects.get_or_create(
                user=shopper,
                provider='stripe_managed',
                defaults={
                    'payment_type': 'other',
                    'last_four': '0000',
                    'display_name': 'Stripe - flamingo',
                    'exp_month': 12,
                    'exp_year': 2030,
                    'is_default': False
                }
            )

            if created:
                print(f"✅ Méthode de paiement créée: {payment_method.display_name}")
            else:
                print(f"✅ Méthode de paiement existante: {payment_method.display_name}")

            print("\n🛒 5. Création du panier et commandes...")

            # Créer un panier pour l'utilisateur
            cart, created = Cart.objects.get_or_create(
                user=shopper,
                defaults={}
            )

            if created:
                print(f"✅ Panier créé pour {shopper.username}")
            else:
                print(f"✅ Panier existant pour {shopper.username}")

            # Créer quelques commandes d'exemple
            if created_products:
                vogue_tshirt = created_products[0]  # Premier produit

                # Commande 1 - Payée
                order1, created = Order.objects.get_or_create(
                    user=shopper,
                    product=vogue_tshirt,
                    size='XL',
                    defaults={
                        'quantity': 1,
                        'is_paid': True,
                        'paid_at': datetime.now()
                    }
                )

                if created:
                    cart.orders.add(order1)
                    print(f"✅ Commande créée: {vogue_tshirt.name} taille XL (payée)")

                # Commande 2 - Payée
                order2, created = Order.objects.get_or_create(
                    user=shopper,
                    product=vogue_tshirt,
                    size='L',
                    defaults={
                        'quantity': 2,
                        'is_paid': True,
                        'paid_at': datetime.now()
                    }
                )

                if created:
                    cart.orders.add(order2)
                    print(f"✅ Commande créée: {vogue_tshirt.name} taille L x2 (payée)")

            print("\n💰 6. Création de la transaction...")

            # Créer la transaction Stripe
            transaction_obj, created = Transaction.objects.get_or_create(
                stripe_payment_intent_id='pi_3RrFswBXVrQp99vf1exsnXjz',
                defaults={
                    'order_ids': '2,1',
                    'provider': 'stripe',
                    'amount': Decimal('119.97'),
                    'currency': 'EUR',
                    'fee_amount': Decimal('0.00'),
                    'status': 'succeeded',
                    'description': 'Paiement Stripe - 2 articles',
                    'user': shopper,
                    'payment_method': payment_method
                }
            )

            if created:
                print(f"✅ Transaction créée: {transaction_obj.amount}€ ({transaction_obj.status})")
            else:
                print(f"✅ Transaction existante: {transaction_obj.amount}€")

            print("\n🎉 CRÉATION TERMINÉE AVEC SUCCÈS!")
            print("=" * 60)
            print(f"✅ Utilisateur admin: flamingo")
            print(f"✅ Catégories: {len(categories_data)}")
            print(f"✅ Produits: {len(products_data)}")
            print(f"✅ Méthode de paiement: Stripe")
            print(f"✅ Commandes: 2 (payées)")
            print(f"✅ Transaction: 119.97€")

            return True

    except Exception as e:
        print(f"❌ Erreur lors de la création des données: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_essential_data()

    if success:
        print(f"\n🚀 VOTRE BOUTIQUE EST PRÊTE!")
        print("📱 Prochaines étapes:")
        print("   1. python manage.py runserver")
        print("   2. Aller sur http://localhost:8000/")
        print("   3. Admin: http://localhost:8000/admin/")
        print("   4. Login: flamingo / votre_mot_de_passe_admin")
    else:
        print(f"\n❌ Échec de la création des données")
        sys.exit(1)
