"""
Tests unitaires pour l'application store.
Tests des modèles, vues et fonctions critiques du e-commerce.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
from store.models import Product, Order, Cart
from store.views import (
    check_stock_availability,
    get_user_cart_quantity,
    get_cart_summary,
)

User = get_user_model()


class ProductModelTest(TestCase):
    """Tests du modèle Product"""

    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=Decimal("29.99"),
            stock=10,
            description="Un produit de test",
        )

    def test_product_creation(self):
        """Test de création d'un produit"""
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, Decimal("29.99"))
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.is_available)

    def test_product_is_available(self):
        """Test de la propriété is_available"""
        # Produit avec stock
        self.assertTrue(self.product.is_available)

        # Produit sans stock
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available)

    def test_product_formatted_price(self):
        """Test du formatage du prix"""
        self.assertEqual(self.product.formatted_price, "29.99 €")

    def test_product_get_absolute_url(self):
        """Test de l'URL absolue du produit"""
        expected_url = reverse("store:product_detail", kwargs={"slug": "test-product"})
        self.assertEqual(self.product.get_absolute_url(), expected_url)


class OrderModelTest(TestCase):
    """Tests du modèle Order"""

    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=Decimal("25.00"), stock=5
        )

    def test_order_creation(self):
        """Test de création d'une commande"""
        order = Order.objects.create(user=self.user, product=self.product, quantity=2)

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.product, self.product)
        self.assertEqual(order.quantity, 2)
        self.assertFalse(order.ordered)  # Par défaut non commandé

    def test_order_total_price(self):
        """Test du calcul du prix total"""
        order = Order.objects.create(user=self.user, product=self.product, quantity=3)

        expected_total = Decimal("75.00")  # 3 × 25.00
        self.assertEqual(order.total_price, expected_total)

    def test_order_formatted_total(self):
        """Test du formatage du total"""
        order = Order.objects.create(user=self.user, product=self.product, quantity=2)

        self.assertEqual(order.formatted_total, "50.00 €")


class CartModelTest(TestCase):
    """Tests du modèle Cart"""

    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.product1 = Product.objects.create(
            name="Product 1", slug="product-1", price=Decimal("20.00"), stock=10
        )
        self.product2 = Product.objects.create(
            name="Product 2", slug="product-2", price=Decimal("30.00"), stock=5
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        """Test de création d'un panier"""
        self.assertEqual(self.cart.user, self.user)
        self.assertTrue(self.cart.is_empty)

    def test_cart_with_orders(self):
        """Test du panier avec des commandes"""
        # Ajouter des commandes au panier
        order1 = Order.objects.create(
            user=self.user, product=self.product1, quantity=2, ordered=False
        )
        order2 = Order.objects.create(
            user=self.user, product=self.product2, quantity=1, ordered=False
        )

        self.cart.orders.add(order1, order2)

        # Tests des propriétés du panier
        self.assertEqual(self.cart.total_items, 3)  # 2 + 1
        self.assertEqual(self.cart.total_price, Decimal("70.00"))  # (2×20) + (1×30)
        self.assertEqual(self.cart.formatted_total, "70.00 €")
        self.assertFalse(self.cart.is_empty)

    def test_cart_only_non_ordered_items(self):
        """Test que le panier ne compte que les articles non commandés"""
        # Commande non finalisée
        order1 = Order.objects.create(
            user=self.user, product=self.product1, quantity=2, ordered=False
        )
        # Commande finalisée
        order2 = Order.objects.create(
            user=self.user,
            product=self.product2,
            quantity=1,
            ordered=True,  # Déjà commandé
        )

        self.cart.orders.add(order1, order2)

        # Seule la commande non finalisée doit être comptée
        self.assertEqual(self.cart.total_items, 2)
        self.assertEqual(self.cart.total_price, Decimal("40.00"))


class StockUtilityFunctionsTest(TestCase):
    """Tests des fonctions utilitaires de gestion de stock"""

    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=Decimal("25.00"), stock=5
        )

    def test_check_stock_availability_sufficient(self):
        """Test de vérification de stock - stock suffisant"""
        result = check_stock_availability(self.product, 3)

        self.assertTrue(result["available"])
        self.assertEqual(result["max_quantity"], 5)

    def test_check_stock_availability_insufficient(self):
        """Test de vérification de stock - stock insuffisant"""
        result = check_stock_availability(self.product, 10)

        self.assertFalse(result["available"])
        self.assertEqual(result["max_quantity"], 5)
        self.assertIn("Stock insuffisant", result["message"])

    def test_check_stock_availability_no_stock(self):
        """Test de vérification de stock - pas de stock"""
        self.product.stock = 0
        self.product.save()

        result = check_stock_availability(self.product, 1)

        self.assertFalse(result["available"])
        self.assertEqual(result["max_quantity"], 0)
        self.assertIn("n'est plus en stock", result["message"])

    def test_get_user_cart_quantity(self):
        """Test de récupération de la quantité dans le panier"""
        # Aucune commande dans le panier
        quantity = get_user_cart_quantity(self.user, self.product)
        self.assertEqual(quantity, 0)

        # Ajouter une commande
        Order.objects.create(
            user=self.user, product=self.product, quantity=3, ordered=False
        )

        quantity = get_user_cart_quantity(self.user, self.product)
        self.assertEqual(quantity, 3)

        # Commande finalisée ne doit pas être comptée
        Order.objects.filter(user=self.user, product=self.product).update(ordered=True)

        quantity = get_user_cart_quantity(self.user, self.product)
        self.assertEqual(quantity, 0)


class CartSummaryTest(TestCase):
    """Tests de la fonction get_cart_summary"""

    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.product1 = Product.objects.create(
            name="Product 1", slug="product-1", price=Decimal("15.00"), stock=10
        )
        self.product2 = Product.objects.create(
            name="Product 2", slug="product-2", price=Decimal("25.00"), stock=5
        )

    def test_get_cart_summary_empty(self):
        """Test du résumé d'un panier vide"""
        summary = get_cart_summary(self.user)

        self.assertEqual(summary["total_items"], 0)
        self.assertEqual(summary["total_price"], 0)
        self.assertTrue(summary["is_empty"])
        self.assertEqual(len(summary["orders"]), 0)

    def test_get_cart_summary_with_items(self):
        """Test du résumé d'un panier avec articles"""
        # Créer un panier avec des commandes
        cart = Cart.objects.create(user=self.user)

        order1 = Order.objects.create(
            user=self.user, product=self.product1, quantity=2, ordered=False
        )
        order2 = Order.objects.create(
            user=self.user, product=self.product2, quantity=1, ordered=False
        )

        cart.orders.add(order1, order2)

        summary = get_cart_summary(self.user)

        self.assertEqual(summary["total_items"], 3)  # 2 + 1
        self.assertEqual(summary["total_price"], Decimal("55.00"))  # (2×15) + (1×25)
        self.assertFalse(summary["is_empty"])
        self.assertEqual(len(summary["orders"]), 2)


class ViewsIntegrationTest(TestCase):
    """Tests d'intégration des vues principales"""

    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=Decimal("29.99"),
            stock=5,
            description="Produit de test",
        )

    def test_index_view(self):
        """Test de la page d'accueil"""
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

    def test_product_detail_view(self):
        """Test de la page détail produit"""
        response = self.client.get(
            reverse("store:product_detail", kwargs={"slug": "test-product"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertContains(response, "29,99")

    def test_add_to_cart_authenticated(self):
        """Test d'ajout au panier - utilisateur connecté"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("add_to_cart", kwargs={"slug": "test-product"})
        )

        # Redirection après ajout
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'article est dans le panier
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 1)

    def test_add_to_cart_unauthenticated(self):
        """Test d'ajout au panier - utilisateur non connecté"""
        response = self.client.post(
            reverse("add_to_cart", kwargs={"slug": "test-product"})
        )

        # Redirection vers login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_cart_view_authenticated(self):
        """Test de la vue panier - utilisateur connecté"""
        self.client.login(username="testuser", password="testpass123")

        # Ajouter un article au panier
        cart = Cart.objects.create(user=self.user)
        order = Order.objects.create(
            user=self.user, product=self.product, quantity=2, ordered=False
        )
        cart.orders.add(order)

        response = self.client.get(reverse("store:cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertContains(response, "2")  # Quantité


class SecurityTest(TestCase):
    """Tests de sécurité"""

    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=Decimal("29.99"), stock=5
        )

    def test_user_cannot_modify_other_user_cart(self):
        """Test qu'un utilisateur ne peut pas modifier le panier d'un autre"""
        # User1 ajoute un article
        self.client.login(username="user1", password="testpass123")
        self.client.post(reverse("add_to_cart", kwargs={"slug": "test-product"}))

        # Récupérer l'ID de la commande de user1
        cart1 = Cart.objects.get(user=self.user1)
        order_id = cart1.orders.first().id

        # User2 se connecte et essaie de modifier la commande de user1
        self.client.login(username="user2", password="testpass123")

        response = self.client.get(
            reverse("increase_quantity", kwargs={"order_id": order_id})
        )

        # Cela devrait échouer (404 ou redirection)
        self.assertIn(response.status_code, [302, 404])

        # Vérifier que la commande de user1 n'a pas été modifiée
        cart1.refresh_from_db()
        original_order = cart1.orders.first()
        self.assertEqual(original_order.quantity, 1)  # Quantité inchangée
