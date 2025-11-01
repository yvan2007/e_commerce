"""
Tests pour les modèles de l'application e-commerce
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal

from accounts.models import User, UserProfile, VendorProfile
from products.models import Product, Category, Tag, ProductImage, ProductReview
from orders.models import Order, OrderItem, Cart, CartItem
from payment_system.models import PaymentMethod, PaymentTransaction, MobileMoneyAccount
# from notifications.models import NotificationTemplate, Notification, NotificationPreference

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'user_type': 'client',
            'phone_number': '+225123456789',
            'country_code': '+225'
        }
    
    def test_create_user(self):
        """Test de création d'un utilisateur"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user_type, 'client')
        self.assertEqual(user.country_code, '+225')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_create_vendor(self):
        """Test de création d'un vendeur"""
        vendor_data = self.user_data.copy()
        vendor_data['user_type'] = 'vendeur'
        vendor_data['username'] = 'testvendor'
        vendor_data['email'] = 'vendor@example.com'
        
        vendor = User.objects.create_user(**vendor_data)
        self.assertEqual(vendor.user_type, 'vendeur')
        self.assertTrue(vendor.is_vendor())
        self.assertFalse(vendor.is_client())
    
    def test_create_admin(self):
        """Test de création d'un administrateur"""
        admin_data = self.user_data.copy()
        admin_data['user_type'] = 'admin'
        admin_data['username'] = 'testadmin'
        admin_data['email'] = 'admin@example.com'
        admin_data['is_superuser'] = True
        
        admin = User.objects.create_user(**admin_data)
        self.assertEqual(admin.user_type, 'admin')
        self.assertTrue(admin.is_admin_user())
    
    def test_get_display_name(self):
        """Test de la méthode get_display_name"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_display_name(), 'Test User')
        
        # Test avec seulement le prénom
        user.first_name = 'Test'
        user.last_name = ''
        user.save()
        self.assertEqual(user.get_display_name(), 'Test')
        
        # Test avec seulement le username
        user.first_name = ''
        user.save()
        self.assertEqual(user.get_display_name(), 'testuser')
    
    def test_get_full_phone_number(self):
        """Test de la méthode get_full_phone_number"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_phone_number(), '+225123456789')
        
        # Test sans numéro de téléphone
        user.phone_number = ''
        user.save()
        self.assertIsNone(user.get_full_phone_number())


class ProductModelTest(TestCase):
    """Tests pour le modèle Product"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test product description',
            'price': Decimal('100.00'),
            'vendor': self.user,
            'category': self.category,
            'stock': 10
        }
    
    def test_create_product(self):
        """Test de création d'un produit"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.price, Decimal('100.00'))
        self.assertEqual(product.vendor, self.user)
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.status, 'draft')
    
    def test_product_slug_generation(self):
        """Test de génération automatique du slug"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.slug, 'test-product')
    
    def test_product_sku_generation(self):
        """Test de génération automatique du SKU"""
        product = Product.objects.create(**self.product_data)
        self.assertTrue(product.sku.startswith('SKU_'))
    
    def test_product_availability(self):
        """Test de la disponibilité du produit"""
        product = Product.objects.create(**self.product_data)
        
        # Produit disponible
        self.assertTrue(product.is_available())
        
        # Produit en rupture de stock
        product.stock = 0
        product.save()
        self.assertFalse(product.is_available())
        
        # Produit non publié
        product.stock = 10
        product.status = 'draft'
        product.save()
        self.assertFalse(product.is_available())


class OrderModelTest(TestCase):
    """Tests pour le modèle Order"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            price=Decimal('100.00'),
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
        
        self.order_data = {
            'user': self.user,
            'status': 'pending',
            'shipping_address': 'Test Address',
            'shipping_cost': Decimal('10.00'),
            'tax_amount': Decimal('5.00'),
            'total_amount': Decimal('115.00')
        }
    
    def test_create_order(self):
        """Test de création d'une commande"""
        order = Order.objects.create(**self.order_data)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, Decimal('115.00'))
    
    def test_order_with_items(self):
        """Test de création d'une commande avec des articles"""
        order = Order.objects.create(**self.order_data)
        
        # Ajouter un article
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)
        self.assertEqual(order.items.first().quantity, 2)


class PaymentModelTest(TestCase):
    """Tests pour les modèles de paiement"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='Moov Money',
            type='mobile_money',
            is_active=True
        )
    
    def test_create_payment_method(self):
        """Test de création d'une méthode de paiement"""
        self.assertEqual(self.payment_method.name, 'Moov Money')
        self.assertEqual(self.payment_method.type, 'mobile_money')
        self.assertTrue(self.payment_method.is_active)
    
    def test_create_mobile_money_account(self):
        """Test de création d'un compte Mobile Money"""
        account = MobileMoneyAccount.objects.create(
            user=self.user,
            provider='moov',
            phone_number='+225123456789',
            is_verified=True
        )
        
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.provider, 'moov')
        self.assertEqual(account.phone_number, '+225123456789')
        self.assertTrue(account.is_verified)


class NotificationModelTest(TestCase):
    """Tests pour les modèles de notification"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            type='email',
            trigger_type='order_placed',
            subject='Test Subject',
            content='Test Content'
        )
    
    def test_create_notification_template(self):
        """Test de création d'un template de notification"""
        self.assertEqual(self.template.name, 'Test Template')
        self.assertEqual(self.template.type, 'email')
        self.assertEqual(self.template.trigger_type, 'order_placed')
    
    def test_create_notification(self):
        """Test de création d'une notification"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            type='email',
            subject='Test Subject',
            content='Test Content'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.template, self.template)
        self.assertEqual(notification.status, 'pending')
        self.assertFalse(notification.is_read)
    
    def test_create_notification_preference(self):
        """Test de création des préférences de notification"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            email_order_updates=True,
            sms_order_updates=False
        )
        
        self.assertEqual(prefs.user, self.user)
        self.assertTrue(prefs.email_order_updates)
        self.assertFalse(prefs.sms_order_updates)


class CartModelTest(TestCase):
    """Tests pour le modèle Cart"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            price=Decimal('100.00'),
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
    
    def test_create_cart(self):
        """Test de création d'un panier"""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.items.count(), 0)
    
    def test_add_item_to_cart(self):
        """Test d'ajout d'un article au panier"""
        cart = Cart.objects.create(user=self.user)
        
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.total_price, Decimal('200.00'))
    
    def test_cart_total(self):
        """Test du calcul du total du panier"""
        cart = Cart.objects.create(user=self.user)
        
        # Ajouter plusieurs articles
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        # Créer un autre produit
        product2 = Product.objects.create(
            name='Test Product 2',
            description='Test product 2 description',
            price=Decimal('50.00'),
            vendor=self.vendor,
            category=self.category,
            stock=5,
            status='published'
        )
        
        CartItem.objects.create(
            cart=cart,
            product=product2,
            quantity=1
        )
        
        # Le total devrait être 200 + 50 = 250
        self.assertEqual(cart.get_total(), Decimal('250.00'))


# Tests d'intégration
class IntegrationTest(TestCase):
    """Tests d'intégration pour le flux complet"""
    
    def setUp(self):
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username='vendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        # Créer une catégorie
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Créer un produit
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            price=Decimal('100.00'),
            vendor=self.vendor_user,
            category=self.category,
            stock=10,
            status='published'
        )
    
    def test_complete_order_flow(self):
        """Test du flux complet de commande"""
        # 1. Créer un panier
        cart = Cart.objects.create(user=self.client_user)
        
        # 2. Ajouter un produit au panier
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        # 3. Créer une commande
        order = Order.objects.create(
            user=self.client_user,
            status='pending',
            shipping_address='Test Address',
            shipping_cost=Decimal('10.00'),
            tax_amount=Decimal('5.00'),
            total_amount=Decimal('215.00')
        )
        
        # 4. Ajouter l'article à la commande
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        
        # 5. Vérifier que tout est correct
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal('215.00'))
        self.assertEqual(order.status, 'pending')
        
        # 6. Mettre à jour le statut de la commande
        order.status = 'confirmed'
        order.save()
        
        self.assertEqual(order.status, 'confirmed')
    
    def test_product_review_flow(self):
        """Test du flux d'avis produit"""
        # Créer un avis
        review = ProductReview.objects.create(
            product=self.product,
            user=self.client_user,
            rating=5,
            title='Excellent produit',
            comment='Très satisfait de cet achat'
        )
        
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.client_user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Excellent produit')
        
        # Vérifier que l'avis est approuvé par défaut
        self.assertTrue(review.is_approved)