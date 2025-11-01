"""
Tests pour les vues de l'application e-commerce
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import json

from accounts.models import User, UserProfile, VendorProfile
from products.models import Product, Category, Tag
from orders.models import Order, OrderItem, Cart, CartItem
from payment_system.models import PaymentMethod, PaymentTransaction, MobileMoneyAccount

User = get_user_model()


class AuthenticationViewTest(TestCase):
    """Tests pour les vues d'authentification"""
    
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'client',
            'phone_number': '+225123456789',
            'country_code': '+225',
            'terms_accepted': True
        }
    
    def test_user_registration_get(self):
        """Test de l'affichage du formulaire d'inscription"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inscription')
    
    def test_user_registration_post_client(self):
        """Test de l'inscription d'un client"""
        response = self.client.post(reverse('accounts:register'), self.user_data)
        self.assertEqual(response.status_code, 302)  # Redirection après inscription
        
        # Vérifier que l'utilisateur a été créé
        user = User.objects.get(username='testuser')
        self.assertEqual(user.user_type, 'client')
        self.assertEqual(user.email, 'test@example.com')
    
    def test_user_registration_post_vendor(self):
        """Test de l'inscription d'un vendeur"""
        vendor_data = self.user_data.copy()
        vendor_data['user_type'] = 'vendeur'
        vendor_data['username'] = 'testvendor'
        vendor_data['email'] = 'vendor@example.com'
        vendor_data['business_name'] = 'Test Business'
        vendor_data['business_description'] = 'Test business description'
        
        response = self.client.post(reverse('accounts:register'), vendor_data)
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que le vendeur a été créé
        vendor = User.objects.get(username='testvendor')
        self.assertEqual(vendor.user_type, 'vendeur')
        self.assertTrue(hasattr(vendor, 'vendor_profile'))
    
    def test_user_login_get(self):
        """Test de l'affichage du formulaire de connexion"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connexion')
    
    def test_user_login_post(self):
        """Test de la connexion d'un utilisateur"""
        # Créer un utilisateur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        
        # Tenter de se connecter
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirection après connexion
    
    def test_user_logout(self):
        """Test de la déconnexion d'un utilisateur"""
        # Créer et connecter un utilisateur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Se déconnecter
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)


class ProductViewTest(TestCase):
    """Tests pour les vues de produits"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un vendeur
        self.vendor = User.objects.create_user(
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
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
    
    def test_product_list_view(self):
        """Test de la vue de liste des produits"""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_product_detail_view(self):
        """Test de la vue de détail d'un produit"""
        response = self.client.get(reverse('products:product_detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_category_list_view(self):
        """Test de la vue de liste des catégories"""
        response = self.client.get(reverse('products:category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Category')
    
    def test_home_page_view(self):
        """Test de la vue de la page d'accueil"""
        response = self.client.get(reverse('products:home_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'KefyStore')


class CartViewTest(TestCase):
    """Tests pour les vues du panier"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        # Créer un vendeur
        self.vendor = User.objects.create_user(
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
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
    
    def test_cart_view_authenticated(self):
        """Test de la vue du panier pour un utilisateur connecté"""
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mon Panier')
    
    def test_cart_view_unauthenticated(self):
        """Test de la vue du panier pour un utilisateur non connecté"""
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion
    
    def test_add_to_cart_ajax(self):
        """Test d'ajout au panier via AJAX"""
        self.client.login(username='client', password='testpass123')
        
        response = self.client.post(reverse('products:add_to_cart', kwargs={'product_id': self.product.pk}), {
            'quantity': 2
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Vérifier que l'article a été ajouté au panier
        cart = Cart.objects.get(user=self.client_user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)
    
    def test_remove_from_cart_ajax(self):
        """Test de suppression du panier via AJAX"""
        self.client.login(username='client', password='testpass123')
        
        # Ajouter un article au panier
        cart = Cart.objects.create(user=self.client_user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        # Supprimer l'article
        response = self.client.post(reverse('products:remove_from_cart', kwargs={'item_id': cart_item.pk}), 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Vérifier que l'article a été supprimé
        self.assertEqual(cart.items.count(), 0)


class OrderViewTest(TestCase):
    """Tests pour les vues de commande"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        # Créer un vendeur
        self.vendor = User.objects.create_user(
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
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
        
        # Créer un panier avec un article
        self.cart = Cart.objects.create(user=self.client_user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_checkout_view_authenticated(self):
        """Test de la vue de checkout pour un utilisateur connecté"""
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Commande')
    
    def test_checkout_view_unauthenticated(self):
        """Test de la vue de checkout pour un utilisateur non connecté"""
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion
    
    def test_checkout_post(self):
        """Test de soumission du formulaire de checkout"""
        self.client.login(username='client', password='testpass123')
        
        checkout_data = {
            'shipping_address': 'Test Address',
            'shipping_city': 'Test City',
            'shipping_postal_code': '12345',
            'payment_method': 'cash_on_delivery',
            'notes': 'Test notes'
        }
        
        response = self.client.post(reverse('orders:checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)  # Redirection après création de commande
        
        # Vérifier que la commande a été créée
        order = Order.objects.get(user=self.client_user)
        self.assertEqual(order.shipping_address, 'Test Address')
        self.assertEqual(order.status, 'pending')
    
    def test_order_list_view(self):
        """Test de la vue de liste des commandes"""
        self.client.login(username='client', password='testpass123')
        
        # Créer une commande
        order = Order.objects.create(
            user=self.client_user,
            status='pending',
            shipping_address='Test Address',
            total_amount=Decimal('200.00')
        )
        
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mes Commandes')


class DashboardViewTest(TestCase):
    """Tests pour les vues du dashboard"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un administrateur
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            user_type='admin',
            is_superuser=True
        )
        
        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username='vendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
    
    def test_admin_dashboard_access(self):
        """Test d'accès au dashboard administrateur"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tableau de Bord Administrateur')
    
    def test_admin_dashboard_unauthorized(self):
        """Test d'accès non autorisé au dashboard administrateur"""
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la page d'accueil
    
    def test_vendor_dashboard_access(self):
        """Test d'accès au dashboard vendeur"""
        self.client.login(username='vendor', password='testpass123')
        response = self.client.get(reverse('dashboard:vendor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tableau de Bord Vendeur')
    
    def test_vendor_dashboard_unauthorized(self):
        """Test d'accès non autorisé au dashboard vendeur"""
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('dashboard:vendor_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la page d'accueil


class SearchViewTest(TestCase):
    """Tests pour les vues de recherche"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un vendeur
        self.vendor = User.objects.create_user(
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
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
    
    def test_search_products(self):
        """Test de recherche de produits"""
        response = self.client.get(reverse('search:search'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_search_with_filters(self):
        """Test de recherche avec filtres"""
        response = self.client.get(reverse('search:search'), {
            'q': 'Test',
            'category': self.category.id,
            'min_price': 50,
            'max_price': 150
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_search_suggestions_api(self):
        """Test de l'API de suggestions de recherche"""
        response = self.client.get(reverse('products:search_suggestions'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)


class PaymentViewTest(TestCase):
    """Tests pour les vues de paiement"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        # Créer une commande
        self.order = Order.objects.create(
            user=self.client_user,
            status='pending',
            shipping_address='Test Address',
            total_amount=Decimal('200.00')
        )
        
        # Créer une méthode de paiement
        self.payment_method = PaymentMethod.objects.create(
            name='Moov Money',
            type='mobile_money',
            is_active=True
        )
    
    def test_payment_method_list(self):
        """Test de la liste des méthodes de paiement"""
        response = self.client.get(reverse('payment_system:payment_methods'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Moov Money')
    
    def test_initiate_payment(self):
        """Test d'initiation d'un paiement"""
        self.client.login(username='client', password='testpass123')
        
        response = self.client.post(reverse('payment_system:initiate_payment', kwargs={'order_id': self.order.id}), {
            'payment_method': self.payment_method.id
        })
        
        self.assertEqual(response.status_code, 200)
        # Vérifier qu'une transaction de paiement a été créée
        self.assertTrue(PaymentTransaction.objects.filter(order=self.order).exists())


class WishlistViewTest(TestCase):
    """Tests pour les vues de wishlist"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        # Créer un vendeur
        self.vendor = User.objects.create_user(
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
            vendor=self.vendor,
            category=self.category,
            stock=10,
            status='published'
        )
    
    def test_wishlist_view_authenticated(self):
        """Test de la vue de wishlist pour un utilisateur connecté"""
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('wishlist:wishlist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ma Liste de Souhaits')
    
    def test_wishlist_view_unauthenticated(self):
        """Test de la vue de wishlist pour un utilisateur non connecté"""
        response = self.client.get(reverse('wishlist:wishlist'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion
    
    def test_add_to_wishlist_ajax(self):
        """Test d'ajout à la wishlist via AJAX"""
        self.client.login(username='client', password='testpass123')
        
        response = self.client.post(reverse('wishlist:add_to_wishlist', kwargs={'product_id': self.product.pk}), 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_remove_from_wishlist_ajax(self):
        """Test de suppression de la wishlist via AJAX"""
        self.client.login(username='client', password='testpass123')
        
        # Ajouter à la wishlist
        self.client.post(reverse('wishlist:add_to_wishlist', kwargs={'product_id': self.product.pk}), 
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Supprimer de la wishlist
        response = self.client.post(reverse('wishlist:remove_from_wishlist', kwargs={'product_id': self.product.pk}), 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])