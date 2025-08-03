"""
Tests unitaires pour l'application accounts.
Tests du modèle utilisateur personnalisé et des vues d'authentification.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
        # Profil complet (100%)
        self.assertEqual(self.user.profile_completion_percentage, 100.0)

        self.assertEqual(self.user.username, "testuser")
class ShopperModelTest(TestCase):
        # Sans prénom
        user_no_firstname = User.objects.create_user(
            username="nofirstname",
            email="nofirstname@example.com",
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
    def test_profile_completion_percentage(self):
        """Test du pourcentage de complétion du profil"""
        # Profil complet (100%)
        self.assertEqual(self.user.profile_completion_percentage, 100.0)
        )
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
            password="testpass123",
        # Vérifier que l'utilisateur est connecté
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        # Vérifier que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(username="newuser").exists())
        # Créer un produit et des commandes
        product = Product.objects.create(
    def test_logout_view(self):
        """Test de déconnexion"""
        # Se connecter d'abord
        self.client.login(username="testuser", password="testpass123")

        # Se déconnecter
        response = self.client.post(reverse("logout"))

        # Redirection après déconnexion
        self.assertEqual(response.status_code, 302)
        """Test d'inscription réussie"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "complexpassword123",
            "password2": "complexpassword123",
            "first_name": "Nouveau",
            "last_name": "Utilisateur",
        }
            "password2": "complexpassword123",
        response = self.client.post(reverse("signup"), user_data)
        # Redirection vers login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
    def test_profile_view_authenticated(self):
        """Test de la vue profil pour utilisateur connecté"""
        self.client.login(username="testuser", password="testpass123")
        self.assertEqual(self.user.last_name, "Dupont")
        self.assertTrue(self.user.check_password("testpass123"))
        # Avec prénom et nom
        expected = "Jean Dupont (testuser)"
        self.assertEqual(str(self.user), expected)
            username="incomplete",
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jean")
        self.assertContains(response, "Dupont")

    def test_profile_view_unauthenticated(self):
        """Test de la vue profil pour utilisateur non connecté"""
        """Configuration initiale"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )
        self.assertEqual(self.user.full_name, "Jean Dupont")
            "testuser",  # Similaire au nom d'utilisateur
            "12345678",  # Trop simple
        ]
        self.assertEqual(str(user_no_name), "noname")
            "123456",
            "testuser",  # Similaire au nom d'utilisateur
class AuthenticationViewsTest(TestCase):
    """Tests des vues d'authentification"""

        for weak_password in weak_passwords:
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
        for weak_password in weak_passwords:
            user_data = {
                "username": "testweakpass",
                "email": "weak@example.com",
                "password1": weak_password,
                "password2": weak_password,
            }
        response = self.client.get(reverse("profile"))
            response = self.client.post(reverse("signup"), user_data)

            # L'inscription devrait échouer
            self.assertNotEqual(response.status_code, 302)
            # L'utilisateur ne devrait pas être créé
            self.assertFalse(User.objects.filter(username="testweakpass").exists())


class UserIntegrationTest(TestCase):
    """Tests d'intégration utilisateur avec le reste du système"""

        # Reste sur la page de login
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion")

    def test_signup_view_get(self):
        """Test de l'affichage de la page d'inscription"""
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
        # Créer des commandes finalisées
        response = self.client.post(reverse("signup"), user_data)
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="integrationuser",
            email="integration@example.com",
            password="testpass123",
            first_name="Integration",
            last_name="User",
        )
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_logout_view(self):
        """Test de déconnexion"""
        # Se connecter d'abord
    def test_user_workflow_complete(self):
        """Test du workflow complet utilisateur"""
        from store.models import Product, Cart

        # 1. Créer un produit
        product = Product.objects.create(
            name="Integration Product",
            slug="integration-product",
        # Sans prénom et nom
        user_no_name = User.objects.create_user(
            username="noname", email="noname@example.com", password="testpass123"
        )
    def test_user_cannot_access_other_profile(self):
        """Test qu'un utilisateur ne peut pas accéder au profil d'un autre"""
        # Se connecter avec user1
        self.client.login(username="user1", password="testpass123")

