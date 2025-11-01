"""
Configuration pytest pour les tests
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import User, UserProfile, VendorProfile
from products.models import Product, Category, Tag
from orders.models import Order, OrderItem, Cart, CartItem
from payment_system.models import PaymentMethod, PaymentTransaction
from notifications.models import NotificationTemplate, NotificationPreference

User = get_user_model()


@pytest.fixture
def client():
    """Client de test Django"""
    return Client()


@pytest.fixture
def user_data():
    """Données de base pour un utilisateur"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'testpass123',
        'user_type': 'client',
        'phone_number': '+225123456789',
        'country_code': '+225'
    }


@pytest.fixture
def vendor_data():
    """Données de base pour un vendeur"""
    return {
        'username': 'testvendor',
        'email': 'vendor@example.com',
        'first_name': 'Test',
        'last_name': 'Vendor',
        'password': 'testpass123',
        'user_type': 'vendeur',
        'phone_number': '+225123456789',
        'country_code': '+225',
        'business_name': 'Test Business',
        'business_description': 'Test business description'
    }


@pytest.fixture
def admin_data():
    """Données de base pour un administrateur"""
    return {
        'username': 'testadmin',
        'email': 'admin@example.com',
        'first_name': 'Test',
        'last_name': 'Admin',
        'password': 'testpass123',
        'user_type': 'admin',
        'phone_number': '+225123456789',
        'country_code': '+225',
        'is_superuser': True
    }


@pytest.fixture
def client_user(user_data):
    """Utilisateur client pour les tests"""
    user = User.objects.create_user(**user_data)
    UserProfile.objects.create(user=user)
    NotificationPreference.objects.create(user=user)
    return user


@pytest.fixture
def vendor_user(vendor_data):
    """Utilisateur vendeur pour les tests"""
    user = User.objects.create_user(**vendor_data)
    UserProfile.objects.create(user=user)
    VendorProfile.objects.create(
        user=user,
        business_name=vendor_data['business_name'],
        business_description=vendor_data['business_description'],
        is_approved=True
    )
    NotificationPreference.objects.create(user=user)
    return user


@pytest.fixture
def admin_user(admin_data):
    """Utilisateur administrateur pour les tests"""
    user = User.objects.create_user(**admin_data)
    UserProfile.objects.create(user=user)
    NotificationPreference.objects.create(user=user)
    return user


@pytest.fixture
def category():
    """Catégorie de produit pour les tests"""
    return Category.objects.create(
        name='Test Category',
        description='Test category description',
        slug='test-category'
    )


@pytest.fixture
def tag():
    """Tag de produit pour les tests"""
    return Tag.objects.create(
        name='Test Tag',
        description='Test tag description',
        slug='test-tag'
    )


@pytest.fixture
def product(vendor_user, category):
    """Produit pour les tests"""
    return Product.objects.create(
        name='Test Product',
        description='Test product description',
        price=Decimal('100.00'),
        vendor=vendor_user,
        category=category,
        stock=10,
        status='published',
        sku='TEST-001'
    )


@pytest.fixture
def product_with_image(vendor_user, category):
    """Produit avec image pour les tests"""
    product = Product.objects.create(
        name='Test Product with Image',
        description='Test product description',
        price=Decimal('150.00'),
        vendor=vendor_user,
        category=category,
        stock=5,
        status='published',
        sku='TEST-002'
    )
    return product


@pytest.fixture
def cart(client_user):
    """Panier pour les tests"""
    return Cart.objects.create(user=client_user)


@pytest.fixture
def cart_item(cart, product):
    """Article de panier pour les tests"""
    return CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=2
    )


@pytest.fixture
def order(client_user):
    """Commande pour les tests"""
    return Order.objects.create(
        user=client_user,
        status='pending',
        shipping_address='Test Address',
        shipping_cost=Decimal('10.00'),
        tax_amount=Decimal('5.00'),
        total_amount=Decimal('215.00')
    )


@pytest.fixture
def order_item(order, product):
    """Article de commande pour les tests"""
    return OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        price=product.price
    )


@pytest.fixture
def payment_method():
    """Méthode de paiement pour les tests"""
    return PaymentMethod.objects.create(
        name='Moov Money',
        type='mobile_money',
        is_active=True,
        fees_percentage=Decimal('2.50')
    )


@pytest.fixture
def payment_transaction(order, client_user, payment_method):
    """Transaction de paiement pour les tests"""
    return PaymentTransaction.objects.create(
        order=order,
        user=client_user,
        payment_method=payment_method,
        amount=order.total_amount,
        fees=Decimal('5.38'),
        total_amount=Decimal('220.38'),
        status='pending'
    )


@pytest.fixture
def notification_template():
    """Template de notification pour les tests"""
    return NotificationTemplate.objects.create(
        name='Test Template',
        type='email',
        trigger_type='order_placed',
        subject='Test Subject',
        content='Test Content'
    )


@pytest.fixture
def notification(client_user, notification_template):
    """Notification pour les tests"""
    return Notification.objects.create(
        user=client_user,
        template=notification_template,
        type='email',
        subject='Test Subject',
        content='Test Content'
    )


@pytest.fixture
def authenticated_client(client, client_user):
    """Client authentifié pour les tests"""
    client.force_login(client_user)
    return client


@pytest.fixture
def authenticated_vendor_client(client, vendor_user):
    """Client vendeur authentifié pour les tests"""
    client.force_login(vendor_user)
    return client


@pytest.fixture
def authenticated_admin_client(client, admin_user):
    """Client administrateur authentifié pour les tests"""
    client.force_login(admin_user)
    return client


@pytest.fixture
def sample_products(vendor_user, category):
    """Plusieurs produits pour les tests"""
    products = []
    for i in range(5):
        product = Product.objects.create(
            name=f'Test Product {i+1}',
            description=f'Test product {i+1} description',
            price=Decimal(f'{100 + i*10}.00'),
            vendor=vendor_user,
            category=category,
            stock=10,
            status='published',
            sku=f'TEST-{i+1:03d}'
        )
        products.append(product)
    return products


@pytest.fixture
def sample_categories():
    """Plusieurs catégories pour les tests"""
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f'Test Category {i+1}',
            description=f'Test category {i+1} description',
            slug=f'test-category-{i+1}'
        )
        categories.append(category)
    return categories


@pytest.fixture
def sample_orders(client_user):
    """Plusieurs commandes pour les tests"""
    orders = []
    for i in range(3):
        order = Order.objects.create(
            user=client_user,
            status='pending',
            shipping_address=f'Test Address {i+1}',
            shipping_cost=Decimal('10.00'),
            tax_amount=Decimal('5.00'),
            total_amount=Decimal(f'{100 + i*50}.00')
        )
        orders.append(order)
    return orders


@pytest.fixture
def sample_payment_methods():
    """Plusieurs méthodes de paiement pour les tests"""
    methods = []
    payment_types = [
        ('Moov Money', 'mobile_money'),
        ('Orange Money', 'mobile_money'),
        ('MTN Money', 'mobile_money'),
        ('Wave', 'wave'),
        ('Carte Bancaire', 'bank_card'),
        ('Paiement à la Livraison', 'cash_on_delivery'),
    ]
    
    for name, payment_type in payment_types:
        method = PaymentMethod.objects.create(
            name=name,
            type=payment_type,
            is_active=True,
            fees_percentage=Decimal('2.50') if payment_type != 'cash_on_delivery' else Decimal('0.00')
        )
        methods.append(method)
    return methods


@pytest.fixture
def sample_notification_templates():
    """Plusieurs templates de notification pour les tests"""
    templates = []
    template_data = [
        ('Commande passée', 'email', 'order_placed'),
        ('Commande confirmée', 'email', 'order_confirmed'),
        ('Commande expédiée', 'email', 'order_shipped'),
        ('Commande livrée', 'email', 'order_delivered'),
        ('Paiement réussi', 'email', 'payment_success'),
        ('Paiement échoué', 'email', 'payment_failed'),
        ('Vendeur approuvé', 'email', 'vendor_approved'),
        ('Vendeur rejeté', 'email', 'vendor_rejected'),
    ]
    
    for name, notification_type, trigger_type in template_data:
        template = NotificationTemplate.objects.create(
            name=name,
            type=notification_type,
            trigger_type=trigger_type,
            subject=f'{name} - KefyStore',
            content=f'Contenu pour {name}'
        )
        templates.append(template)
    return templates


@pytest.fixture
def sample_cart_items(cart, sample_products):
    """Plusieurs articles de panier pour les tests"""
    items = []
    for i, product in enumerate(sample_products):
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=i + 1
        )
        items.append(item)
    return items


@pytest.fixture
def sample_order_items(order, sample_products):
    """Plusieurs articles de commande pour les tests"""
    items = []
    for i, product in enumerate(sample_products):
        item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=i + 1,
            price=product.price
        )
        items.append(item)
    return items


@pytest.fixture
def sample_payment_transactions(sample_orders, client_user, sample_payment_methods):
    """Plusieurs transactions de paiement pour les tests"""
    transactions = []
    for i, order in enumerate(sample_orders):
        transaction = PaymentTransaction.objects.create(
            order=order,
            user=client_user,
            payment_method=sample_payment_methods[i % len(sample_payment_methods)],
            amount=order.total_amount,
            fees=Decimal('5.00'),
            total_amount=order.total_amount + Decimal('5.00'),
            status='pending'
        )
        transactions.append(transaction)
    return transactions


@pytest.fixture
def sample_notifications(client_user, sample_notification_templates):
    """Plusieurs notifications pour les tests"""
    notifications = []
    for i, template in enumerate(sample_notification_templates):
        notification = Notification.objects.create(
            user=client_user,
            template=template,
            type=template.type,
            subject=f'{template.subject} #{i+1}',
            content=f'{template.content} #{i+1}'
        )
        notifications.append(notification)
    return notifications


# Fixtures pour les tests d'intégration
@pytest.fixture
def complete_order_flow(client_user, vendor_user, category, sample_products):
    """Flux complet de commande pour les tests d'intégration"""
    # Créer un panier
    cart = Cart.objects.create(user=client_user)
    
    # Ajouter des produits au panier
    cart_items = []
    for product in sample_products[:3]:  # Prendre les 3 premiers produits
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        cart_items.append(item)
    
    # Créer une commande
    order = Order.objects.create(
        user=client_user,
        status='pending',
        shipping_address='Test Address',
        shipping_cost=Decimal('10.00'),
        tax_amount=Decimal('5.00'),
        total_amount=Decimal('500.00')
    )
    
    # Ajouter les articles à la commande
    order_items = []
    for item in cart_items:
        order_item = OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
        order_items.append(order_item)
    
    return {
        'cart': cart,
        'cart_items': cart_items,
        'order': order,
        'order_items': order_items
    }


@pytest.fixture
def complete_payment_flow(complete_order_flow, sample_payment_methods):
    """Flux complet de paiement pour les tests d'intégration"""
    order = complete_order_flow['order']
    payment_method = sample_payment_methods[0]  # Moov Money
    
    transaction = PaymentTransaction.objects.create(
        order=order,
        user=order.user,
        payment_method=payment_method,
        amount=order.total_amount,
        fees=Decimal('12.50'),
        total_amount=order.total_amount + Decimal('12.50'),
        status='pending'
    )
    
    return {
        **complete_order_flow,
        'payment_transaction': transaction
    }


# Fixtures pour les tests de performance
@pytest.fixture
def large_dataset(vendor_user, sample_categories):
    """Dataset large pour les tests de performance"""
    products = []
    for i in range(100):
        category = sample_categories[i % len(sample_categories)]
        product = Product.objects.create(
            name=f'Product {i+1}',
            description=f'Description for product {i+1}',
            price=Decimal(f'{10 + i}.00'),
            vendor=vendor_user,
            category=category,
            stock=100,
            status='published',
            sku=f'PROD-{i+1:04d}'
        )
        products.append(product)
    return products


# Fixtures pour les tests de sécurité
@pytest.fixture
def malicious_input():
    """Données malveillantes pour les tests de sécurité"""
    return {
        'sql_injection': "'; DROP TABLE products; --",
        'xss_script': '<script>alert("XSS")</script>',
        'html_injection': '<img src="x" onerror="alert(1)">',
        'path_traversal': '../../../etc/passwd',
        'command_injection': '; rm -rf /',
    }


# Fixtures pour les tests de validation
@pytest.fixture
def invalid_data():
    """Données invalides pour les tests de validation"""
    return {
        'invalid_email': 'not-an-email',
        'invalid_phone': '123',
        'negative_price': Decimal('-100.00'),
        'empty_string': '',
        'too_long_string': 'x' * 1000,
        'invalid_date': 'not-a-date',
    }