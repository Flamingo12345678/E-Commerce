"""
Tests unitaires pour l'application accounts.
Tests du modèle utilisateur personnalisé et des vues d'authentification.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

User = get_user_model()


class ShopperModelTest(TestCase):
    """Tests du modèle Shopper (utilisateur personnalisé)"""

    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Jean",
            last_name="Dupont",
            phone_number="0123456789",
            address="123 Rue de la Paix, 75001 Paris",
        )

    def test_user_creation(self):
        """Test de création d'un utilisateur"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.first_name, "Jean")
        self.assertEqual(self.user.last_name, "Dupont")
        self.assertTrue(self.user.check_password("testpass123"))

    def test_full_name_property(self):
        """Test de la propriété full_name"""
        # Avec prénom et nom
        self.assertEqual(self.user.full_name, "Jean Dupont")

        # Sans prénom et nom
        user_no_name = User.objects.create_user(
            username="noname", email="noname@example.com", password="testpass123"
        )
        self.assertEqual(user_no_name.full_name, "noname")

    def test_display_name_property(self):
        """Test de la propriété display_name"""
        # Avec prénom
        self.assertEqual(self.user.display_name, "Jean")

        # Sans prénom
        user_no_firstname = User.objects.create_user(
            username="nofirstname",
            email="nofirstname@example.com",
            password="testpass123",
            last_name="Doe",
        )
        self.assertEqual(user_no_firstname.display_name, "nofirstname")

    def test_has_complete_profile(self):
        """Test de la propriété has_complete_profile"""
        # Profil complet
        self.assertTrue(self.user.has_complete_profile)

        # Profil incomplet (sans téléphone)
        user_incomplete = User.objects.create_user(
            username="incomplete",
            email="incomplete@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
            # phone_number et address manquants
        )
        self.assertFalse(user_incomplete.has_complete_profile)

    def test_profile_completion_percentage(self):
        """Test du pourcentage de complétion du profil"""
        # Profil complet (100%)
        self.assertEqual(self.user.profile_completion_percentage, 100.0)

        # Profil à 60% (3 champs sur 5)
        user_partial = User.objects.create_user(
            username="partial",
            email="partial@example.com",
            password="testpass123",
            first_name="Jane",
            # last_name, phone_number, address manquants
        )
        self.assertEqual(user_partial.profile_completion_percentage, 40.0)  # 2/5 = 40%

    def test_get_total_orders(self):
        """Test du nombre total de commandes"""
        from store.models import Product, Order

        # Créer un produit et des commandes
        product = Product.objects.create(
            name="Test Product", slug="test-product", price=Decimal("25.00"), stock=10
        )

        # Commandes finalisées
        Order.objects.create(user=self.user, product=product, quantity=2, ordered=True)
        Order.objects.create(user=self.user, product=product, quantity=1, ordered=True)

        # Commande non finalisée (ne doit pas être comptée)
        Order.objects.create(user=self.user, product=product, quantity=1, ordered=False)

        self.assertEqual(self.user.get_total_orders(), 2)

    def test_get_total_spent(self):
        """Test du montant total dépensé"""
        from store.models import Product, Order

        product1 = Product.objects.create(
            name="Product 1", slug="product-1", price=Decimal("20.00"), stock=10
        )
        product2 = Product.objects.create(
            name="Product 2", slug="product-2", price=Decimal("30.00"), stock=5
        )

        # Commandes finalisées
        Order.objects.create(
            user=self.user, product=product1, quantity=2, ordered=True  # 2 × 20 = 40
        )
        Order.objects.create(
            user=self.user, product=product2, quantity=1, ordered=True  # 1 × 30 = 30
        )

        # Commande non finalisée (ne doit pas être comptée)
        Order.objects.create(
            user=self.user, product=product1, quantity=5, ordered=False
        )

        expected_total = Decimal("70.00")  # 40 + 30
        self.assertEqual(self.user.get_total_spent(), expected_total)

    def test_newsletter_subscription_default(self):
        """Test que l'abonnement newsletter est False par défaut"""
        user = User.objects.create_user(
            username="newslettertest",
            email="newsletter@example.com",
            password="testpass123",
        )
        self.assertFalse(user.newsletter_subscription)

    def test_str_representation(self):
        """Test de la représentation string de l'utilisateur"""
        # Avec prénom et nom
        expected = "Jean Dupont (testuser)"
        self.assertEqual(str(self.user), expected)

        # Sans prénom et nom
        user_no_name = User.objects.create_user(
            username="noname", email="noname@example.com", password="testpass123"
        )
        self.assertEqual(str(user_no_name), "noname")


class AuthenticationViewsTest(TestCase):
    """Tests des vues d'authentification"""

    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Jean",
            last_name="Dupont",
        )

    def test_login_view_get(self):
        """Test de l'affichage de la page de connexion"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion")

    def test_login_view_post_success(self):
        """Test de connexion réussie"""
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )

        # Redirection après connexion réussie
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est connecté
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)

    def test_login_view_post_failure(self):
        """Test de connexion échouée"""
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "wrongpassword"}
        )

        # Reste sur la page de login
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion")

    def test_signup_view_get(self):
        """Test de l'affichage de la page d'inscription"""
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Créer un compte")

    def test_signup_view_post_success(self):
        """Test d'inscription réussie"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "complexpassword123",
            "password2": "complexpassword123",
            "first_name": "Nouveau",
            "last_name": "Utilisateur",
        }

        response = self.client.post(reverse("signup"), user_data)

        # Redirection après inscription réussie
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_logout_view(self):
        """Test de déconnexion"""
        # Se connecter d'abord
        self.client.login(username="testuser", password="testpass123")

        # Se déconnecter
        response = self.client.post(reverse("logout"))

        # Redirection après déconnexion
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        """Test de la vue profil pour utilisateur connecté"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jean")
        self.assertContains(response, "Dupont")

    def test_profile_view_unauthenticated(self):
        """Test de la vue profil pour utilisateur non connecté"""
        response = self.client.get(reverse("profile"))

        # Redirection vers login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class UserSecurityTest(TestCase):
    """Tests de sécurité utilisateur"""

    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

    def test_user_cannot_access_other_profile(self):
        """Test qu'un utilisateur ne peut pas accéder au profil d'un autre"""
        # Se connecter avec user1
        self.client.login(username="user1", password="testpass123")

        # La vue profil ne devrait montrer que les infos de user1
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

        # Le contexte devrait contenir user1, pas user2
        self.assertEqual(response.context["user"], self.user1)
        self.assertNotEqual(response.context["user"], self.user2)

    def test_password_change_requires_authentication(self):
        """Test que le changement de mot de passe nécessite une authentification"""
        response = self.client.get(reverse("change_password"))

        # Redirection vers login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_strong_password_validation(self):
        """Test de validation des mots de passe forts"""
        weak_passwords = [
            "password",
            "123456",
            "testuser",  # Similaire au nom d'utilisateur
            "12345678",  # Trop simple
        ]

        for weak_password in weak_passwords:
            user_data = {
                "username": "testweakpass",
                "email": "weak@example.com",
                "password1": weak_password,
                "password2": weak_password,
            }

            response = self.client.post(reverse("signup"), user_data)

            # L'inscription devrait échouer
            self.assertNotEqual(response.status_code, 302)
            # L'utilisateur ne devrait pas être créé
            self.assertFalse(User.objects.filter(username="testweakpass").exists())


class UserIntegrationTest(TestCase):
    """Tests d'intégration utilisateur avec le reste du système"""

    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="integrationuser",
            email="integration@example.com",
            password="testpass123",
            first_name="Integration",
            last_name="User",
        )

    def test_user_workflow_complete(self):
        """Test du workflow complet utilisateur"""
        from store.models import Product, Cart

        # 1. Créer un produit
        product = Product.objects.create(
            name="Integration Product",
            slug="integration-product",
            price=Decimal("19.99"),
            stock=3,
        )

        # 2. Se connecter
        login_success = self.client.login(
            username="integrationuser", password="testpass123"
        )
        self.assertTrue(login_success)

        # 3. Ajouter au panier
        response = self.client.post(
            reverse("store:add_to_cart", kwargs={"slug": "integration-product"})
        )
        self.assertEqual(response.status_code, 302)

        # 4. Vérifier le panier
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 1)

        # 5. Aller à la page panier
        response = self.client.get(reverse("store:cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Product")

        # 6. Voir le profil
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration")

    def test_user_statistics_accuracy(self):
        """Test de la précision des statistiques utilisateur"""
        from store.models import Product, Order

        # Créer des produits
        product1 = Product.objects.create(
            name="Stats Product 1",
            slug="stats-product-1",
            price=Decimal("10.00"),
            stock=10,
        )
        product2 = Product.objects.create(
            name="Stats Product 2",
            slug="stats-product-2",
            price=Decimal("25.00"),
            stock=5,
        )

        # Créer des commandes finalisées
        Order.objects.create(user=self.user, product=product1, quantity=3, ordered=True)
        Order.objects.create(user=self.user, product=product2, quantity=2, ordered=True)

        # Créer une commande non finalisée (ne doit pas compter)
        Order.objects.create(
            user=self.user, product=product1, quantity=5, ordered=False
        )

        # Vérifier les statistiques
        self.assertEqual(self.user.get_total_orders(), 2)
        expected_spent = Decimal("80.00")  # (3×10) + (2×25)
        self.assertEqual(self.user.get_total_spent(), expected_spent)
