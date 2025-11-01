import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch

from .models import Order, OrderItem, Cart, CartItem, ShippingAddress, OrderStatusHistory
from .forms import CheckoutForm, ShippingAddressForm
from products.models import Category, Product

User = get_user_model()


class OrderModelTest(TestCase):
    """Tests pour le modèle Order"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(name='Électronique')
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            vendor=self.vendor,
            category=self.category,
            price=100.00,
            stock=10,
            status='published'
        )
    
    def test_create_order(self):
        """Test de création d'une commande"""
        order = Order.objects.create(
            user=self.user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            shipping_cost=10.00,
            tax_amount=5.00,
            total_amount=115.00
        )
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.shipping_first_name, 'John')
        self.assertEqual(order.payment_method, 'cash')
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, Decimal('115.00'))
        self.assertTrue(order.order_number.startswith('CMD-'))
    
    def test_order_str(self):
        """Test de la représentation string de la commande"""
        order = Order.objects.create(
            user=self.user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            total_amount=100.00
        )
        
        expected = f"Commande {order.order_number}"
        self.assertEqual(str(order), expected)
    
    def test_order_can_be_cancelled(self):
        """Test de vérification si une commande peut être annulée"""
        order = Order.objects.create(
            user=self.user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            total_amount=100.00
        )
        
        # Commande en attente peut être annulée
        self.assertTrue(order.can_be_cancelled())
        
        # Commande confirmée peut être annulée
        order.status = 'confirmed'
        order.save()
        self.assertTrue(order.can_be_cancelled())
        
        # Commande livrée ne peut pas être annulée
        order.status = 'delivered'
        order.save()
        self.assertFalse(order.can_be_cancelled())
    
    def test_order_status_display_color(self):
        """Test de la couleur d'affichage du statut"""
        order = Order.objects.create(
            user=self.user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            total_amount=100.00
        )
        
        self.assertEqual(order.get_status_display_color(), 'warning')  # pending
        
        order.status = 'delivered'
        order.save()
        self.assertEqual(order.get_status_display_color(), 'success')


class OrderItemModelTest(TestCase):
    """Tests pour le modèle OrderItem"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(name='Électronique')
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            vendor=self.vendor,
            category=self.category,
            price=100.00,
            stock=10,
            status='published'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            total_amount=100.00
        )
    
    def test_create_order_item(self):
        """Test de création d'un article de commande"""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=100.00,
            total_price=200.00
        )
        
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal('100.00'))
        self.assertEqual(order_item.total_price, Decimal('200.00'))
    
    def test_order_item_total_price_calculation(self):
        """Test de calcul automatique du prix total"""
        order_item = OrderItem(
            order=self.order,
            product=self.product,
            quantity=3,
            unit_price=50.00
        )
        order_item.save()
        
        expected_total = Decimal('50.00') * 3
        self.assertEqual(order_item.total_price, expected_total)
    
    def test_order_item_str(self):
        """Test de la représentation string de l'article de commande"""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=100.00,
            total_price=200.00
        )
        
        expected = f"{self.product.name} x 2"
        self.assertEqual(str(order_item), expected)


class CartModelTest(TestCase):
    """Tests pour le modèle Cart"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(name='Électronique')
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            vendor=self.vendor,
            category=self.category,
            price=100.00,
            stock=10,
            status='published'
        )
    
    def test_create_cart(self):
        """Test de création d'un panier"""
        cart = Cart.objects.create(user=self.user)
        
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.get_total_items(), 0)
        self.assertEqual(cart.get_total_price(), 0)
    
    def test_cart_with_items(self):
        """Test de panier avec des articles"""
        cart = Cart.objects.create(user=self.user)
        
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        self.assertEqual(cart.get_total_items(), 2)
        self.assertEqual(cart.get_total_price(), Decimal('200.00'))
    
    def test_cart_clear(self):
        """Test de vidage du panier"""
        cart = Cart.objects.create(user=self.user)
        
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        self.assertEqual(cart.get_total_items(), 2)
        
        cart.clear()
        self.assertEqual(cart.get_total_items(), 0)


class CartItemModelTest(TestCase):
    """Tests pour le modèle CartItem"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(name='Électronique')
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            vendor=self.vendor,
            category=self.category,
            price=100.00,
            stock=10,
            status='published'
        )
        
        self.cart = Cart.objects.create(user=self.user)
    
    def test_create_cart_item(self):
        """Test de création d'un article de panier"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        
        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 3)
        self.assertEqual(cart_item.get_unit_price(), Decimal('100.00'))
        self.assertEqual(cart_item.get_total_price(), Decimal('300.00'))
    
    def test_cart_item_str(self):
        """Test de la représentation string de l'article de panier"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        
        expected = f"{self.product.name} x 3"
        self.assertEqual(str(cart_item), expected)


class ShippingAddressModelTest(TestCase):
    """Tests pour le modèle ShippingAddress"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
    
    def test_create_shipping_address(self):
        """Test de création d'une adresse de livraison"""
        address = ShippingAddress.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address='123 Test Street',
            city='Abidjan',
            country='Côte d\'Ivoire'
        )
        
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.first_name, 'John')
        self.assertEqual(address.last_name, 'Doe')
        self.assertEqual(address.city, 'Abidjan')
        self.assertFalse(address.is_default)
    
    def test_default_address_handling(self):
        """Test de gestion de l'adresse par défaut"""
        # Créer une première adresse
        address1 = ShippingAddress.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address='123 Test Street',
            city='Abidjan',
            country='Côte d\'Ivoire'
        )
        
        # Créer une deuxième adresse par défaut
        address2 = ShippingAddress.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Doe',
            phone='0987654321',
            address='456 Another Street',
            city='Yamoussoukro',
            country='Côte d\'Ivoire',
            is_default=True
        )
        
        # Vérifier que la première adresse n'est plus par défaut
        address1.refresh_from_db()
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)
    
    def test_shipping_address_str(self):
        """Test de la représentation string de l'adresse"""
        address = ShippingAddress.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address='123 Test Street',
            city='Abidjan',
            country='Côte d\'Ivoire'
        )
        
        expected = "John Doe - Abidjan"
        self.assertEqual(str(address), expected)


class OrderStatusHistoryModelTest(TestCase):
    """Tests pour le modèle OrderStatusHistory"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            total_amount=100.00
        )
    
    def test_create_order_status_history(self):
        """Test de création d'un historique de statut"""
        history = OrderStatusHistory.objects.create(
            order=self.order,
            status='confirmed',
            notes='Commande confirmée par le vendeur',
            created_by=self.user
        )
        
        self.assertEqual(history.order, self.order)
        self.assertEqual(history.status, 'confirmed')
        self.assertEqual(history.notes, 'Commande confirmée par le vendeur')
        self.assertEqual(history.created_by, self.user)
    
    def test_order_status_history_str(self):
        """Test de la représentation string de l'historique"""
        history = OrderStatusHistory.objects.create(
            order=self.order,
            status='confirmed',
            notes='Commande confirmée',
            created_by=self.user
        )
        
        expected = f"{self.order.order_number} - Confirmée"
        self.assertEqual(str(history), expected)


class OrderFormsTest(TestCase):
    """Tests pour les formulaires de commande"""
    
    def test_valid_checkout_form(self):
        """Test de formulaire de commande valide"""
        form_data = {
            'shipping_first_name': 'John',
            'shipping_last_name': 'Doe',
            'shipping_phone': '1234567890',
            'shipping_address': '123 Test Street',
            'shipping_city': 'Abidjan',
            'payment_method': 'cash',
            'terms_accepted': True
        }
        
        form = CheckoutForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_phone_checkout_form(self):
        """Test de formulaire de commande avec téléphone invalide"""
        form_data = {
            'shipping_first_name': 'John',
            'shipping_last_name': 'Doe',
            'shipping_phone': 'invalid-phone',
            'shipping_address': '123 Test Street',
            'shipping_city': 'Abidjan',
            'payment_method': 'cash',
            'terms_accepted': True
        }
        
        form = CheckoutForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('shipping_phone', form.errors)
    
    def test_billing_address_validation(self):
        """Test de validation de l'adresse de facturation"""
        form_data = {
            'shipping_first_name': 'John',
            'shipping_last_name': 'Doe',
            'shipping_phone': '1234567890',
            'shipping_address': '123 Test Street',
            'shipping_city': 'Abidjan',
            'payment_method': 'cash',
            'billing_different': True,
            'billing_address': '',  # Adresse de facturation vide
            'terms_accepted': True
        }
        
        form = CheckoutForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_valid_shipping_address_form(self):
        """Test de formulaire d'adresse de livraison valide"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '1234567890',
            'address': '123 Test Street',
            'city': 'Abidjan',
            'country': 'Côte d\'Ivoire',
            'is_default': True
        }
        
        form = ShippingAddressForm(data=form_data)
        self.assertTrue(form.is_valid())


class OrderViewsTest(TestCase):
    """Tests pour les vues de commande"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        self.vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        self.category = Category.objects.create(name='Électronique')
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            vendor=self.vendor,
            category=self.category,
            price=100.00,
            stock=10,
            status='published'
        )
    
    def test_cart_view_authenticated(self):
        """Test de vue du panier pour un utilisateur connecté"""
        self.client.login(username='testclient', password='testpass123')
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 200)
    
    def test_cart_view_unauthenticated(self):
        """Test de vue du panier pour un utilisateur non connecté"""
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion
    
    def test_checkout_view_authenticated(self):
        """Test de vue de commande pour un utilisateur connecté"""
        self.client.login(username='testclient', password='testpass123')
        
        # Créer un panier avec des articles
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 200)
    
    def test_checkout_view_empty_cart(self):
        """Test de vue de commande avec panier vide"""
        self.client.login(username='testclient', password='testpass123')
        
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 200)
        # Le formulaire devrait être affiché même avec un panier vide
    
    def test_order_list_view_authenticated(self):
        """Test de vue de liste des commandes pour un utilisateur connecté"""
        self.client.login(username='testclient', password='testpass123')
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_order_list_view_unauthenticated(self):
        """Test de vue de liste des commandes pour un utilisateur non connecté"""
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la connexion
    
    def test_add_to_cart_authenticated(self):
        """Test d'ajout au panier pour un utilisateur connecté"""
        self.client.login(username='testclient', password='testpass123')
        
        response = self.client.post(
            reverse('products:add_to_cart', args=[self.product.id]),
            {'quantity': 2}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirection après ajout
        
        # Vérifier que l'article a été ajouté au panier
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 2)
    
    def test_remove_from_cart_authenticated(self):
        """Test de suppression du panier pour un utilisateur connecté"""
        self.client.login(username='testclient', password='testpass123')
        
        # Créer un panier avec un article
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        response = self.client.post(
            reverse('products:remove_from_cart', args=[cart_item.id])
        )
        
        self.assertEqual(response.status_code, 302)  # Redirection après suppression
        
        # Vérifier que l'article a été supprimé du panier
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())


@pytest.mark.django_db
class OrderIntegrationTest(TestCase):
    """Tests d'intégration pour les commandes"""
    
    def test_complete_order_flow(self):
        """Test du flux complet de commande"""
        # 1. Créer un utilisateur et un produit
        user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        vendor = User.objects.create_user(
            username='testvendor',
            email='vendor@example.com',
            password='testpass123',
            user_type='vendeur'
        )
        
        category = Category.objects.create(name='Électronique')
        
        product = Product.objects.create(
            name='Test Product',
            description='Test description',
            vendor=vendor,
            category=category,
            price=100.00,
            stock=10,
            status='published'
        )
        
        # 2. Ajouter au panier
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        
        # 3. Passer commande
        client = Client()
        client.login(username='testclient', password='testpass123')
        
        form_data = {
            'shipping_first_name': 'John',
            'shipping_last_name': 'Doe',
            'shipping_phone': '1234567890',
            'shipping_address': '123 Test Street',
            'shipping_city': 'Abidjan',
            'payment_method': 'cash',
            'terms_accepted': True
        }
        
        with patch('orders.views.send_mail'):
            response = client.post(reverse('orders:checkout'), form_data)
            self.assertEqual(response.status_code, 302)  # Redirection après commande
        
        # 4. Vérifier que la commande a été créée
        order = Order.objects.get(user=user)
        self.assertEqual(order.shipping_first_name, 'John')
        self.assertEqual(order.payment_method, 'cash')
        
        # 5. Vérifier que les articles de commande ont été créés
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 1)
        
        order_item = order_items.first()
        self.assertEqual(order_item.product, product)
        self.assertEqual(order_item.quantity, 2)
        
        # 6. Vérifier que le stock a été mis à jour
        product.refresh_from_db()
        self.assertEqual(product.stock, 8)  # 10 - 2
        self.assertEqual(product.sales_count, 2)
        
        # 7. Vérifier que le panier a été vidé
        cart.refresh_from_db()
        self.assertEqual(cart.get_total_items(), 0)
    
    def test_order_status_workflow(self):
        """Test du workflow des statuts de commande"""
        # 1. Créer une commande
        user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            user_type='client'
        )
        
        order = Order.objects.create(
            user=user,
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_phone='1234567890',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash',
            subtotal=100.00,
            total_amount=100.00
        )
        
        # 2. Vérifier le statut initial
        self.assertEqual(order.status, 'pending')
        
        # 3. Confirmer la commande
        order.status = 'confirmed'
        order.save()
        
        # 4. Marquer comme en cours de traitement
        order.status = 'processing'
        order.save()
        
        # 5. Marquer comme expédiée
        from django.utils import timezone
        order.status = 'shipped'
        order.shipped_at = timezone.now()
        order.save()
        
        # 6. Marquer comme livrée
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        
        # 7. Vérifier les dates
        self.assertIsNotNone(order.shipped_at)
        self.assertIsNotNone(order.delivered_at)
        self.assertEqual(order.status, 'delivered')