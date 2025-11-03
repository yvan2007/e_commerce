from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import UserLoginForm, UserRegistrationForm, VendorRegistrationForm
from .models import User, UserProfile, VendorProfile

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User"""

    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpass123",
            "user_type": "client",
            "phone_number": "1234567890",
            "country_code": "+225",
        }

    def test_create_user(self):
        """Test de création d'un utilisateur"""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.user_type, "client")
        self.assertEqual(user.get_full_phone_number(), "+2251234567890")
        self.assertEqual(user.get_display_name(), "Test User")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_vendor(self):
        """Test de création d'un vendeur"""
        vendor_data = self.user_data.copy()
        vendor_data["user_type"] = "vendeur"
        vendor_data["username"] = "testvendor"
        vendor_data["email"] = "vendor@example.com"

        user = User.objects.create_user(**vendor_data)

        self.assertEqual(user.user_type, "vendeur")
        self.assertTrue(hasattr(user, "vendor_profile"))

    def test_user_str(self):
        """Test de la représentation string de l'utilisateur"""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.username} (Client)"
        self.assertEqual(str(user), expected)


class UserProfileModelTest(TestCase):
    """Tests pour le modèle UserProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_user_profile(self):
        """Test de création d'un profil utilisateur"""
        profile = UserProfile.objects.create(
            user=self.user, bio="Test bio", website="https://example.com"
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, "Test bio")
        self.assertEqual(profile.website, "https://example.com")

    def test_user_profile_auto_creation(self):
        """Test de création automatique du profil"""
        # Le profil devrait être créé automatiquement lors de l'inscription
        self.assertTrue(hasattr(self.user, "profile"))


class VendorProfileModelTest(TestCase):
    """Tests pour le modèle VendorProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

    def test_create_vendor_profile(self):
        """Test de création d'un profil vendeur"""
        profile = VendorProfile.objects.create(
            user=self.user,
            business_name="Test Business",
            business_description="Test description",
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.business_name, "Test Business")
        self.assertFalse(profile.is_approved)


class UserRegistrationFormTest(TestCase):
    """Tests pour le formulaire d'inscription"""

    def test_valid_client_registration(self):
        """Test d'inscription client valide"""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "testpass123",
            "password2": "testpass123",
            "phone_number": "1234567890",
            "country_code": "+225",
            "user_type": "client",
            "terms_accepted": True,
        }

        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email_registration(self):
        """Test d'inscription avec email invalide"""
        form_data = {
            "username": "testuser",
            "email": "invalid-email",
            "first_name": "Test",
            "last_name": "User",
            "password1": "testpass123",
            "password2": "testpass123",
            "phone_number": "1234567890",
            "country_code": "+225",
            "user_type": "client",
            "terms_accepted": True,
        }

        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_mismatch(self):
        """Test de mots de passe différents"""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "testpass123",
            "password2": "differentpass",
            "phone_number": "1234567890",
            "country_code": "+225",
            "user_type": "client",
            "terms_accepted": True,
        }

        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class UserViewsTest(TestCase):
    """Tests pour les vues d'authentification"""

    def setUp(self):
        self.client = Client()
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "user_type": "client",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_home_view(self):
        """Test de la vue d'accueil"""
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 200)

    def test_registration_view_get(self):
        """Test de l'affichage du formulaire d'inscription"""
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Créer un compte")

    def test_registration_view_post_client(self):
        """Test d'inscription d'un client"""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "testpass123",
            "password2": "testpass123",
            "phone_number": "1234567890",
            "country_code": "+225",
            "user_type": "client",
            "terms_accepted": True,
        }

        with patch("accounts.views.send_mail") as mock_send_mail:
            response = self.client.post(reverse("accounts:register"), form_data)

            self.assertEqual(response.status_code, 302)  # Redirection après succès
            self.assertTrue(User.objects.filter(username="newuser").exists())
            mock_send_mail.assert_called_once()

    def test_login_view_get(self):
        """Test de l'affichage du formulaire de connexion"""
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion")

    def test_login_view_post_valid(self):
        """Test de connexion avec des identifiants valides"""
        login_data = {"username": "testuser", "password": "testpass123"}

        response = self.client.post(reverse("accounts:login"), login_data)
        self.assertEqual(response.status_code, 302)  # Redirection après connexion

    def test_login_view_post_invalid(self):
        """Test de connexion avec des identifiants invalides"""
        login_data = {"username": "testuser", "password": "wrongpassword"}

        response = self.client.post(reverse("accounts:login"), login_data)
        self.assertEqual(response.status_code, 200)  # Reste sur la page de connexion
        self.assertContains(response, "Connexion")

    def test_profile_view_authenticated(self):
        """Test d'accès au profil pour un utilisateur connecté"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mon Profil")

    def test_profile_view_unauthenticated(self):
        """Test d'accès au profil pour un utilisateur non connecté"""
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion

    def test_logout_view(self):
        """Test de déconnexion"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)  # Redirection après déconnexion


class UserAPITest(TestCase):
    """Tests pour les APIs d'authentification"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_check_username_availability_available(self):
        """Test de vérification de disponibilité du nom d'utilisateur (disponible)"""
        response = self.client.post(
            reverse("accounts:check_username"),
            {"username": "newuser"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["available"])

    def test_check_username_availability_taken(self):
        """Test de vérification de disponibilité du nom d'utilisateur (pris)"""
        response = self.client.post(
            reverse("accounts:check_username"),
            {"username": "testuser"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["available"])

    def test_check_email_availability_available(self):
        """Test de vérification de disponibilité de l'email (disponible)"""
        response = self.client.post(
            reverse("accounts:check_email"),
            {"email": "newuser@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["available"])

    def test_check_email_availability_taken(self):
        """Test de vérification de disponibilité de l'email (pris)"""
        response = self.client.post(
            reverse("accounts:check_email"),
            {"email": "test@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["available"])


class EmailTest(TestCase):
    """Tests pour l'envoi d'emails"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_confirmation_email_sending(self):
        """Test d'envoi d'email de confirmation"""
        with patch("accounts.views.send_mail") as mock_send_mail:
            from accounts.views import UserRegistrationView

            view = UserRegistrationView()
            view.send_confirmation_email(self.user)

            mock_send_mail.assert_called_once()
            call_args = mock_send_mail.call_args
            self.assertIn("Confirmez votre compte", call_args[0][0])
            self.assertIn("test@example.com", call_args[0][3])


@pytest.mark.django_db
class UserIntegrationTest(TestCase):
    """Tests d'intégration pour les utilisateurs"""

    def test_complete_user_registration_flow(self):
        """Test du flux complet d'inscription d'un utilisateur"""
        client = Client()

        # 1. Accéder à la page d'inscription
        response = client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

        # 2. S'inscrire
        form_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "first_name": "Integration",
            "last_name": "User",
            "password1": "testpass123",
            "password2": "testpass123",
            "phone_number": "1234567890",
            "country_code": "+225",
            "user_type": "client",
            "terms_accepted": True,
        }

        with patch("accounts.views.send_mail"):
            response = client.post(reverse("accounts:register"), form_data)
            self.assertEqual(response.status_code, 302)

        # 3. Vérifier que l'utilisateur a été créé
        user = User.objects.get(username="integrationuser")
        self.assertEqual(user.email, "integration@example.com")
        self.assertEqual(user.user_type, "client")

        # 4. Vérifier que les profils ont été créés
        self.assertTrue(hasattr(user, "profile"))

    def test_vendor_registration_flow(self):
        """Test du flux d'inscription d'un vendeur"""
        client = Client()

        form_data = {
            "username": "vendoruser",
            "email": "vendor@example.com",
            "first_name": "Vendor",
            "last_name": "User",
            "password1": "testpass123",
            "password2": "testpass123",
            "phone_number": "1234567890",
            "country_code": "+225",
            "user_type": "vendeur",
            "business_name": "Test Business",
            "business_description": "Test description",
            "terms_accepted": True,
        }

        with patch("accounts.views.send_mail"):
            response = client.post(reverse("accounts:register"), form_data)
            self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur et le profil vendeur ont été créés
        user = User.objects.get(username="vendoruser")
        self.assertEqual(user.user_type, "vendeur")
        self.assertTrue(hasattr(user, "vendor_profile"))
        self.assertEqual(user.vendor_profile.business_name, "Test Business")
