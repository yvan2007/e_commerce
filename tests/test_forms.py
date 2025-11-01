"""
Tests pour les formulaires de l'application KefyStore
"""
import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from products.forms import (
    ProductForm, ProductImageForm, ProductVariantForm, 
    ProductSearchForm, ProductReviewForm, CategoryForm, TagForm
)
from products.models import Category, Tag, Product
from accounts.models import User


class ProductFormTest(TestCase):
    """Tests pour le formulaire ProductForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur"
        )
        self.category = Category.objects.create(
            name="Électronique",
            is_active=True
        )
        self.tag = Tag.objects.create(name="Nouveau")
    
    def test_product_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'name': 'Test Product',
            'category': self.category.id,
            'description': 'Test Description',
            'short_description': 'Short description',
            'price': 1000,
            'stock': 5,
            'status': 'draft',
            'is_featured': False,
            'is_digital': False
        }
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_product_form_invalid_data(self):
        """Test du formulaire avec des données invalides"""
        form_data = {
            'name': '',  # Nom requis
            'category': self.category.id,
            'description': 'Test Description',
            'price': -100,  # Prix négatif
            'stock': -5,  # Stock négatif
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('price', form.errors)
        self.assertIn('stock', form.errors)
    
    def test_product_form_with_tags(self):
        """Test du formulaire avec des tags"""
        form_data = {
            'name': 'Test Product',
            'category': self.category.id,
            'description': 'Test Description',
            'price': 1000,
            'stock': 5,
            'status': 'draft',
            'tags': [self.tag.id]
        }
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_product_form_with_sale_data(self):
        """Test du formulaire avec des données de promotion"""
        form_data = {
            'name': 'Test Product',
            'category': self.category.id,
            'description': 'Test Description',
            'price': 800,
            'original_price': 1000,
            'discount_percentage': 20,
            'is_on_sale': True,
            'stock': 5,
            'status': 'draft'
        }
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())


class ProductImageFormTest(TestCase):
    """Tests pour le formulaire ProductImageForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur"
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            vendor=self.user,
            category=self.category,
            price=1000,
            stock=5,
            status="published"
        )
    
    def test_product_image_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'alt_text': 'Test Image',
            'order': 1,
            'is_active': True
        }
        form = ProductImageForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_product_image_form_invalid_data(self):
        """Test du formulaire avec des données invalides"""
        form_data = {
            'order': -1,  # Ordre négatif
        }
        form = ProductImageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('order', form.errors)


class ProductVariantFormTest(TestCase):
    """Tests pour le formulaire ProductVariantForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur"
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            vendor=self.user,
            category=self.category,
            price=1000,
            stock=5,
            status="published"
        )
    
    def test_product_variant_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'name': 'Rouge',
            'price': 1100,
            'stock': 3,
            'is_active': True
        }
        form = ProductVariantForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_product_variant_form_invalid_data(self):
        """Test du formulaire avec des données invalides"""
        form_data = {
            'name': '',  # Nom requis
            'price': -100,  # Prix négatif
            'stock': -3,  # Stock négatif
        }
        form = ProductVariantForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('price', form.errors)
        self.assertIn('stock', form.errors)


class ProductSearchFormTest(TestCase):
    """Tests pour le formulaire ProductSearchForm"""
    
    def setUp(self):
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.tag = Tag.objects.create(name="Nouveau")
    
    def test_search_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'query': 'Test Product',
            'category': self.category.id,
            'min_price': 100,
            'max_price': 1000,
            'tags': [self.tag.id],
            'sort_by': 'price'
        }
        form = ProductSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_search_form_empty_data(self):
        """Test du formulaire avec des données vides"""
        form_data = {}
        form = ProductSearchForm(data=form_data)
        self.assertTrue(form.is_valid())  # Tous les champs sont optionnels
    
    def test_search_form_invalid_price_range(self):
        """Test du formulaire avec une plage de prix invalide"""
        form_data = {
            'min_price': 1000,
            'max_price': 100,  # Prix min > prix max
        }
        form = ProductSearchForm(data=form_data)
        # Le formulaire devrait être valide car la validation de la plage 
        # est généralement faite dans la vue
        self.assertTrue(form.is_valid())


class ProductReviewFormTest(TestCase):
    """Tests pour le formulaire ProductReviewForm"""
    
    def test_review_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'rating': 5,
            'comment': 'Excellent produit !'
        }
        form = ProductReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_review_form_invalid_rating(self):
        """Test du formulaire avec une note invalide"""
        form_data = {
            'rating': 6,  # Note > 5
            'comment': 'Excellent produit !'
        }
        form = ProductReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
    
    def test_review_form_missing_rating(self):
        """Test du formulaire sans note"""
        form_data = {
            'comment': 'Excellent produit !'
        }
        form = ProductReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
    
    def test_review_form_empty_comment(self):
        """Test du formulaire avec commentaire vide (valide)"""
        form_data = {
            'rating': 5,
            'comment': ''
        }
        form = ProductReviewForm(data=form_data)
        self.assertTrue(form.is_valid())  # Le commentaire est optionnel


class CategoryFormTest(TestCase):
    """Tests pour le formulaire CategoryForm"""
    
    def setUp(self):
        self.parent_category = Category.objects.create(
            name="Électronique",
            is_active=True
        )
    
    def test_category_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'name': 'Smartphones',
            'description': 'Téléphones intelligents',
            'parent': self.parent_category.id,
            'is_active': True,
            'icon': 'fa fa-mobile',
            'order': 1
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_category_form_invalid_data(self):
        """Test du formulaire avec des données invalides"""
        form_data = {
            'name': '',  # Nom requis
            'order': -1,  # Ordre négatif
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('order', form.errors)
    
    def test_category_form_without_parent(self):
        """Test du formulaire sans catégorie parente"""
        form_data = {
            'name': 'Nouvelle Catégorie',
            'description': 'Description',
            'is_active': True,
            'order': 1
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())


class TagFormTest(TestCase):
    """Tests pour le formulaire TagForm"""
    
    def test_tag_form_valid_data(self):
        """Test du formulaire avec des données valides"""
        form_data = {
            'name': 'Nouveau',
            'color': '#28a745'
        }
        form = TagForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_tag_form_invalid_data(self):
        """Test du formulaire avec des données invalides"""
        form_data = {
            'name': '',  # Nom requis
            'color': 'invalid-color'  # Couleur invalide
        }
        form = TagForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_tag_form_default_color(self):
        """Test du formulaire avec couleur par défaut"""
        form_data = {
            'name': 'Test Tag'
        }
        form = TagForm(data=form_data)
        self.assertTrue(form.is_valid())
        # La couleur par défaut devrait être appliquée
        self.assertEqual(form.cleaned_data['color'], '#007bff')


class FormIntegrationTest(TestCase):
    """Tests d'intégration des formulaires"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur"
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.tag = Tag.objects.create(name="Nouveau")
    
    def test_product_creation_workflow(self):
        """Test du workflow complet de création de produit"""
        # 1. Créer le produit
        product_form_data = {
            'name': 'Test Product',
            'category': self.category.id,
            'description': 'Test Description',
            'short_description': 'Short description',
            'price': 1000,
            'stock': 5,
            'status': 'draft',
            'tags': [self.tag.id]
        }
        product_form = ProductForm(data=product_form_data)
        self.assertTrue(product_form.is_valid())
        
        product = product_form.save(commit=False)
        product.vendor = self.user
        product.save()
        product_form.save_m2m()
        
        # 2. Ajouter une image
        image_form_data = {
            'alt_text': 'Test Image',
            'order': 1,
            'is_active': True
        }
        image_form = ProductImageForm(data=image_form_data)
        self.assertTrue(image_form.is_valid())
        
        # 3. Ajouter une variante
        variant_form_data = {
            'name': 'Rouge',
            'price': 1100,
            'stock': 3,
            'is_active': True
        }
        variant_form = ProductVariantForm(data=variant_form_data)
        self.assertTrue(variant_form.is_valid())
        
        # Vérifier que le produit est créé correctement
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.tags.count(), 1)
        self.assertEqual(product.tags.first(), self.tag)
    
    def test_search_workflow(self):
        """Test du workflow de recherche"""
        # Créer des produits de test
        Product.objects.create(
            name="iPhone 15",
            description="Dernier iPhone",
            vendor=self.user,
            category=self.category,
            price=1000000,
            stock=5,
            status="published"
        )
        Product.objects.create(
            name="Samsung Galaxy",
            description="Smartphone Android",
            vendor=self.user,
            category=self.category,
            price=800000,
            stock=3,
            status="published"
        )
        
        # Test de recherche par nom
        search_form_data = {
            'query': 'iPhone',
            'category': self.category.id,
            'sort_by': 'price'
        }
        search_form = ProductSearchForm(data=search_form_data)
        self.assertTrue(search_form.is_valid())
        
        # Test de recherche par prix
        price_search_data = {
            'min_price': 500000,
            'max_price': 900000,
            'sort_by': 'price'
        }
        price_search_form = ProductSearchForm(data=price_search_data)
        self.assertTrue(price_search_form.is_valid())