import os
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from .forms import ProductForm, ProductReviewForm, ProductSearchForm
from .models import Category, Product, ProductImage, ProductReview, ProductVariant, Tag

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests pour le modèle Category"""

    def setUp(self):
        self.category_data = {
            "name": "Électronique",
            "description": "Appareils électroniques",
        }

    def test_create_category(self):
        """Test de création d'une catégorie"""
        category = Category.objects.create(**self.category_data)

        self.assertEqual(category.name, "Électronique")
        self.assertEqual(category.slug, "electronique")
        self.assertTrue(category.is_active)

    def test_category_slug_generation(self):
        """Test de génération automatique du slug"""
        category = Category.objects.create(name="Téléphones Mobiles")
        self.assertEqual(category.slug, "telephones-mobiles")

    def test_category_hierarchy(self):
        """Test de hiérarchie des catégories"""
        parent = Category.objects.create(name="Électronique")
        child = Category.objects.create(name="Téléphones", parent=parent)

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_category_str(self):
        """Test de la représentation string de la catégorie"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(str(category), "Électronique")


class TagModelTest(TestCase):
    """Tests pour le modèle Tag"""

    def test_create_tag(self):
        """Test de création d'une étiquette"""
        tag = Tag.objects.create(name="Nouveau", color="#ff0000")

        self.assertEqual(tag.name, "Nouveau")
        self.assertEqual(tag.slug, "nouveau")
        self.assertEqual(tag.color, "#ff0000")

    def test_tag_slug_generation(self):
        """Test de génération automatique du slug"""
        tag = Tag.objects.create(name="Meilleure Vente")
        self.assertEqual(tag.slug, "meilleure-vente")


class ProductModelTest(TestCase):
    """Tests pour le modèle Product"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

        self.category = Category.objects.create(name="Électronique")

        # Créer une image de test
        self.test_image = self.create_test_image()

    def create_test_image(self):
        """Créer une image de test"""
        image = Image.new("RGB", (100, 100), color="red")
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(tmp_file.name)
        return tmp_file.name

    def tearDown(self):
        """Nettoyer les fichiers de test"""
        if os.path.exists(self.test_image):
            os.unlink(self.test_image)

    def test_create_product(self):
        """Test de création d'un produit"""
        product = Product.objects.create(
            name="iPhone 15",
            description="Nouveau iPhone",
            vendor=self.user,
            category=self.category,
            price=1000.00,
            stock=10,
            main_image=self.test_image,
        )

        self.assertEqual(product.name, "iPhone 15")
        self.assertEqual(product.vendor, self.user)
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.price, 1000.00)
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.status, "draft")
        self.assertFalse(product.is_featured)

    def test_product_slug_generation(self):
        """Test de génération automatique du slug"""
        product = Product.objects.create(
            name="Samsung Galaxy S24",
            description="Nouveau Samsung",
            vendor=self.user,
            category=self.category,
            price=800.00,
            stock=5,
            main_image=self.test_image,
        )

        self.assertEqual(product.slug, "samsung-galaxy-s24")

    def test_product_sku_generation(self):
        """Test de génération automatique du SKU"""
        product = Product.objects.create(
            name="Test Product",
            description="Test",
            vendor=self.user,
            category=self.category,
            price=100.00,
            stock=1,
            main_image=self.test_image,
        )

        self.assertTrue(product.sku.startswith("SKU-"))
        self.assertEqual(len(product.sku), 12)  # SKU- + 8 caractères

    def test_product_discount_percentage(self):
        """Test de calcul du pourcentage de réduction"""
        product = Product.objects.create(
            name="Test Product",
            description="Test",
            vendor=self.user,
            category=self.category,
            price=80.00,
            compare_price=100.00,
            stock=1,
            main_image=self.test_image,
        )

        self.assertEqual(product.get_discount_percentage(), 20)

    def test_product_stock_status(self):
        """Test des statuts de stock"""
        product = Product.objects.create(
            name="Test Product",
            description="Test",
            vendor=self.user,
            category=self.category,
            price=100.00,
            stock=5,
            min_stock=3,
            main_image=self.test_image,
        )

        self.assertTrue(product.is_in_stock())
        self.assertFalse(product.is_low_stock())

        product.stock = 2
        product.save()

        self.assertTrue(product.is_in_stock())
        self.assertTrue(product.is_low_stock())

        product.stock = 0
        product.save()

        self.assertFalse(product.is_in_stock())

    def test_product_str(self):
        """Test de la représentation string du produit"""
        product = Product.objects.create(
            name="Test Product",
            description="Test",
            vendor=self.user,
            category=self.category,
            price=100.00,
            stock=1,
            main_image=self.test_image,
        )

        self.assertEqual(str(product), "Test Product")


class ProductFormTest(TestCase):
    """Tests pour les formulaires de produits"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

        self.category = Category.objects.create(name="Électronique")
        self.tag = Tag.objects.create(name="Nouveau")

    def test_valid_product_form(self):
        """Test de formulaire de produit valide"""
        form_data = {
            "name": "Test Product",
            "description": "Test description",
            "category": self.category.id,
            "price": 100.00,
            "stock": 10,
            "min_stock": 5,
        }

        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_price_form(self):
        """Test de formulaire avec prix invalide"""
        form_data = {
            "name": "Test Product",
            "description": "Test description",
            "category": self.category.id,
            "price": -10.00,  # Prix négatif
            "stock": 10,
            "min_stock": 5,
        }

        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_compare_price_validation(self):
        """Test de validation du prix de comparaison"""
        form_data = {
            "name": "Test Product",
            "description": "Test description",
            "category": self.category.id,
            "price": 100.00,
            "compare_price": 80.00,  # Prix de comparaison inférieur
            "stock": 10,
            "min_stock": 5,
        }

        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("compare_price", form.errors)

    def test_search_form(self):
        """Test du formulaire de recherche"""
        form_data = {"query": "iPhone", "min_price": 500, "max_price": 1000}

        form = ProductSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_search_form_invalid_price_range(self):
        """Test de formulaire de recherche avec plage de prix invalide"""
        form_data = {
            "query": "iPhone",
            "min_price": 1000,
            "max_price": 500,  # Prix min > prix max
        }

        form = ProductSearchForm(data=form_data)
        self.assertFalse(form.is_valid())


class ProductViewsTest(TestCase):
    """Tests pour les vues de produits"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

        self.client_user = User.objects.create_user(
            username="testclient",
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )

        self.category = Category.objects.create(name="Électronique")

        # Créer une image de test
        self.test_image = self.create_test_image()

        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            vendor=self.user,
            category=self.category,
            price=100.00,
            stock=10,
            status="published",
            main_image=self.test_image,
        )

    def create_test_image(self):
        """Créer une image de test"""
        image = Image.new("RGB", (100, 100), color="red")
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(tmp_file.name)
        return tmp_file.name

    def tearDown(self):
        """Nettoyer les fichiers de test"""
        if os.path.exists(self.test_image):
            os.unlink(self.test_image)

    def test_home_view(self):
        """Test de la vue d'accueil"""
        response = self.client.get(reverse("products:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenue sur E-Commerce CI")

    def test_product_list_view(self):
        """Test de la vue de liste des produits"""
        response = self.client.get(reverse("products:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Produits")

    def test_product_detail_view(self):
        """Test de la vue de détail d'un produit"""
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

    def test_product_create_view_authenticated_vendor(self):
        """Test de création de produit par un vendeur connecté"""
        self.client.login(username="testvendor", password="testpass123")
        response = self.client.get(reverse("products:product_create"))
        self.assertEqual(response.status_code, 200)

    def test_product_create_view_unauthenticated(self):
        """Test de création de produit par un utilisateur non connecté"""
        response = self.client.get(reverse("products:product_create"))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion

    def test_product_create_view_client(self):
        """Test de création de produit par un client"""
        self.client.login(username="testclient", password="testpass123")
        response = self.client.get(reverse("products:product_create"))
        self.assertEqual(response.status_code, 403)  # Accès interdit

    def test_add_to_cart_authenticated(self):
        """Test d'ajout au panier par un utilisateur connecté"""
        self.client.login(username="testclient", password="testpass123")

        response = self.client.post(
            reverse("products:add_to_cart", args=[self.product.id]), {"quantity": 2}
        )

        self.assertEqual(response.status_code, 302)  # Redirection après ajout

    def test_add_to_cart_unauthenticated(self):
        """Test d'ajout au panier par un utilisateur non connecté"""
        response = self.client.post(
            reverse("products:add_to_cart", args=[self.product.id]), {"quantity": 2}
        )

        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion

    def test_search_suggestions_api(self):
        """Test de l'API de suggestions de recherche"""
        response = self.client.get(
            reverse("products:search_suggestions"), {"q": "Test"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)
        self.assertIsInstance(data["suggestions"], list)


class ProductReviewTest(TestCase):
    """Tests pour les avis sur les produits"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            user_type="client",
        )

        self.vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

        self.category = Category.objects.create(name="Électronique")

        # Créer une image de test
        self.test_image = self.create_test_image()

        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            vendor=self.vendor,
            category=self.category,
            price=100.00,
            stock=10,
            status="published",
            main_image=self.test_image,
        )

    def create_test_image(self):
        """Créer une image de test"""
        image = Image.new("RGB", (100, 100), color="red")
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(tmp_file.name)
        return tmp_file.name

    def tearDown(self):
        """Nettoyer les fichiers de test"""
        if os.path.exists(self.test_image):
            os.unlink(self.test_image)

    def test_create_product_review(self):
        """Test de création d'un avis sur un produit"""
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Excellent produit",
            comment="Très satisfait de cet achat",
        )

        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_approved)

    def test_review_form_valid(self):
        """Test de formulaire d'avis valide"""
        form_data = {
            "rating": 5,
            "title": "Excellent produit",
            "comment": "Très satisfait de cet achat",
        }

        form = ProductReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_invalid_rating(self):
        """Test de formulaire d'avis avec note invalide"""
        form_data = {
            "rating": 6,  # Note invalide (max 5)
            "title": "Excellent produit",
            "comment": "Très satisfait de cet achat",
        }

        form = ProductReviewForm(data=form_data)
        self.assertFalse(form.is_valid())


@pytest.mark.django_db
class ProductIntegrationTest(TestCase):
    """Tests d'intégration pour les produits"""

    def test_complete_product_creation_flow(self):
        """Test du flux complet de création d'un produit"""
        # 1. Créer un vendeur
        vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

        # 2. Créer une catégorie
        category = Category.objects.create(name="Électronique")

        # 3. Créer un produit
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            vendor=vendor,
            category=category,
            price=100.00,
            stock=10,
            status="published",
        )

        # 4. Vérifier que le produit a été créé correctement
        self.assertEqual(product.vendor, vendor)
        self.assertEqual(product.category, category)
        self.assertEqual(product.status, "published")

        # 5. Vérifier que le vendeur peut voir ses produits
        self.assertIn(product, vendor.products.all())

    def test_product_search_and_filtering(self):
        """Test de recherche et filtrage des produits"""
        # Créer des produits de test
        vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )

        category1 = Category.objects.create(name="Électronique")
        category2 = Category.objects.create(name="Vêtements")

        product1 = Product.objects.create(
            name="iPhone 15",
            description="Nouveau iPhone",
            vendor=vendor,
            category=category1,
            price=1000.00,
            stock=10,
            status="published",
        )

        product2 = Product.objects.create(
            name="T-shirt",
            description="T-shirt en coton",
            vendor=vendor,
            category=category2,
            price=20.00,
            stock=50,
            status="published",
        )

        # Test de recherche par nom
        products = Product.objects.filter(name__icontains="iPhone")
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first(), product1)

        # Test de filtrage par catégorie
        products = Product.objects.filter(category=category1)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first(), product1)

        # Test de filtrage par prix
        products = Product.objects.filter(price__gte=500)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first(), product1)
