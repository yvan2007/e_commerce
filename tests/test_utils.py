"""
Tests pour les utilitaires et fonctions helper de l'application KefyStore
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.mail import outbox
from django.test import TestCase

from notifications.services import (
    send_delivery_confirmation_email,
    send_order_confirmation_email,
    send_order_status_update_email,
    send_password_reset_email,
    send_vendor_notification_email,
    send_welcome_email,
)
from orders.models import Cart, CartItem, Order, OrderItem
from products.models import Category, Product, ProductReview

User = get_user_model()


class EmailNotificationTest(TestCase):
    """Tests pour les notifications email"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            user_type="client",
        )
        self.vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur",
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            vendor=self.vendor,
            category=self.category,
            price=1000,
            stock=5,
            status="published",
        )
        self.order = Order.objects.create(
            user=self.user,
            payment_method="cash",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_phone="+225123456789",
            shipping_address="123 Test Street",
            shipping_city="Abidjan",
            shipping_region="Abidjan",
            shipping_country="Côte d'Ivoire",
            shipping_postal_code="12345",
            subtotal=1000,
            shipping_cost=500,
            tax_amount=150,
            total_amount=1650,
        )
        OrderItem.objects.create(
            order=self.order, product=self.product, quantity=1, price=1000
        )

    def test_send_order_confirmation_email(self):
        """Test d'envoi d'email de confirmation de commande"""
        send_order_confirmation_email(self.order)

        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Confirmation de commande", email.subject)
        self.assertIn(self.order.order_number, email.body)

    def test_send_order_status_update_email(self):
        """Test d'envoi d'email de mise à jour de statut"""
        send_order_status_update_email(self.order, "pending", "confirmed")

        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Mise à jour de commande", email.subject)

    def test_send_delivery_confirmation_email(self):
        """Test d'envoi d'email de confirmation de livraison"""
        send_delivery_confirmation_email(self.order)

        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Livraison confirmée", email.subject)

    def test_send_welcome_email(self):
        """Test d'envoi d'email de bienvenue"""
        send_welcome_email(self.user)

        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Bienvenue", email.subject)

    def test_send_password_reset_email(self):
        """Test d'envoi d'email de réinitialisation de mot de passe"""
        uid = "test_uid"
        token = "test_token"
        send_password_reset_email(self.user, uid, token)

        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Réinitialisation", email.subject)

    def test_send_vendor_notification_email(self):
        """Test d'envoi d'email de notification au vendeur"""
        send_vendor_notification_email(self.order, self.vendor)

        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertEqual(email.to, [self.vendor.email])
        self.assertIn("Nouvelle commande", email.subject)


class ProductUtilityTest(TestCase):
    """Tests pour les utilitaires de produits"""

    def setUp(self):
        self.vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur",
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            vendor=self.vendor,
            category=self.category,
            price=1000,
            stock=5,
            status="published",
        )

    def test_product_discount_calculation(self):
        """Test de calcul des remises"""
        # Test avec prix original
        self.product.original_price = 1200
        self.product.is_on_sale = True
        self.product.save()

        discount = self.product.get_discount_percentage()
        self.assertEqual(discount, 17)  # (1200-1000)/1200 * 100

        # Test avec prix de comparaison
        self.product.original_price = None
        self.product.compare_price = 1100
        self.product.is_on_sale = False
        self.product.save()

        discount = self.product.get_discount_percentage()
        self.assertEqual(discount, 9)  # (1100-1000)/1100 * 100

    def test_product_sale_price_calculation(self):
        """Test de calcul du prix de vente"""
        # Test avec promotion active
        self.product.original_price = 1200
        self.product.is_on_sale = True
        self.product.save()

        sale_price = self.product.calculate_sale_price()
        self.assertEqual(sale_price, 1000)

        # Test sans promotion
        self.product.is_on_sale = False
        self.product.save()

        sale_price = self.product.calculate_sale_price()
        self.assertEqual(sale_price, 1000)

    def test_product_stock_management(self):
        """Test de gestion du stock"""
        # Test stock disponible
        self.assertTrue(self.product.is_in_stock())

        # Test stock faible
        self.product.min_stock = 3
        self.product.stock = 2
        self.product.save()

        self.assertTrue(self.product.is_low_stock())

        # Test rupture de stock
        self.product.stock = 0
        self.product.save()

        self.assertFalse(self.product.is_in_stock())

    def test_product_rating_update(self):
        """Test de mise à jour des notes"""
        # Créer des utilisateurs pour les avis
        user1 = User.objects.create_user(username="user1", email="user1@test.com")
        user2 = User.objects.create_user(username="user2", email="user2@test.com")
        user3 = User.objects.create_user(username="user3", email="user3@test.com")

        # Créer des avis
        ProductReview.objects.create(
            product=self.product, user=user1, rating=5, is_approved=True
        )
        ProductReview.objects.create(
            product=self.product, user=user2, rating=4, is_approved=True
        )
        ProductReview.objects.create(
            product=self.product,
            user=user3,
            rating=3,
            is_approved=False,  # Non approuvé
        )

        # Mettre à jour les notes
        self.product.update_rating()

        # Vérifier que seuls les avis approuvés sont comptés
        self.assertEqual(self.product.rating, 4.5)  # (5+4)/2
        self.assertEqual(self.product.review_count, 2)


class OrderUtilityTest(TestCase):
    """Tests pour les utilitaires de commandes"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            user_type="client",
        )
        self.vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur",
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            vendor=self.vendor,
            category=self.category,
            price=1000,
            stock=5,
            status="published",
        )
        self.order = Order.objects.create(
            user=self.user,
            payment_method="cash",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_phone="+225123456789",
            shipping_address="123 Test Street",
            shipping_city="Abidjan",
            shipping_region="Abidjan",
            shipping_country="Côte d'Ivoire",
            shipping_postal_code="12345",
            subtotal=1000,
            shipping_cost=500,
            tax_amount=150,
            total_amount=1650,
        )

    def test_order_cancellation_logic(self):
        """Test de la logique d'annulation de commande"""
        # Test commande en attente - peut être annulée
        self.assertTrue(self.order.can_be_cancelled())

        # Test commande confirmée - peut être annulée
        self.order.status = "confirmed"
        self.order.save()
        self.assertTrue(self.order.can_be_cancelled())

        # Test commande en cours - ne peut pas être annulée
        self.order.status = "processing"
        self.order.save()
        self.assertFalse(self.order.can_be_cancelled())

        # Test commande expédiée - ne peut pas être annulée
        self.order.status = "shipped"
        self.order.save()
        self.assertFalse(self.order.can_be_cancelled())

    def test_order_status_display_color(self):
        """Test de la couleur d'affichage du statut"""
        # Test statut en attente
        self.assertEqual(self.order.get_status_display_color(), "warning")

        # Test statut confirmé
        self.order.status = "confirmed"
        self.order.save()
        self.assertEqual(self.order.get_status_display_color(), "info")

        # Test statut livré
        self.order.status = "delivered"
        self.order.save()
        self.assertEqual(self.order.get_status_display_color(), "success")

        # Test statut annulé
        self.order.status = "cancelled"
        self.order.save()
        self.assertEqual(self.order.get_status_display_color(), "danger")


class CartUtilityTest(TestCase):
    """Tests pour les utilitaires de panier"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            user_type="client",
        )
        self.vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur",
        )
        self.category = Category.objects.create(name="Électronique", is_active=True)
        self.product1 = Product.objects.create(
            name="Product 1",
            description="Description 1",
            vendor=self.vendor,
            category=self.category,
            price=1000,
            stock=5,
            status="published",
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            description="Description 2",
            vendor=self.vendor,
            category=self.category,
            price=2000,
            stock=3,
            status="published",
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_total_items_calculation(self):
        """Test de calcul du nombre total d'articles"""
        # Panier vide
        self.assertEqual(self.cart.get_total_items(), 0)

        # Ajouter des articles
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)

        self.assertEqual(self.cart.get_total_items(), 3)

    def test_cart_total_price_calculation(self):
        """Test de calcul du prix total"""
        # Panier vide
        self.assertEqual(self.cart.get_total_price(), 0)

        # Ajouter des articles
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)

        # 1000*2 + 2000*1 = 4000
        self.assertEqual(self.cart.get_total_price(), 4000)

    def test_cart_clear_functionality(self):
        """Test de vidage du panier"""
        # Ajouter des articles
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)

        self.assertEqual(self.cart.get_total_items(), 3)

        # Vider le panier
        self.cart.clear()

        self.assertEqual(self.cart.get_total_items(), 0)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    def test_cart_item_price_calculation(self):
        """Test de calcul du prix des articles"""
        # Article avec prix du produit
        cart_item = CartItem.objects.create(
            cart=self.cart, product=self.product1, quantity=3
        )

        self.assertEqual(cart_item.get_unit_price(), 1000)
        self.assertEqual(cart_item.get_total_price(), 3000)

        # Article avec variante
        from products.models import ProductVariant

        variant = ProductVariant.objects.create(
            product=self.product1, name="Rouge", price=1200
        )
        cart_item.variant = variant
        cart_item.save()

        self.assertEqual(cart_item.get_unit_price(), 1200)
        self.assertEqual(cart_item.get_total_price(), 3600)


class DataValidationTest(TestCase):
    """Tests de validation des données"""

    def test_product_price_validation(self):
        """Test de validation des prix de produits"""
        vendor = User.objects.create_user(
            username="testvendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur",
        )
        category = Category.objects.create(name="Électronique", is_active=True)

        # Test prix valide
        product = Product.objects.create(
            name="Valid Product",
            description="Description",
            vendor=vendor,
            category=category,
            price=1000,
            stock=5,
            status="published",
        )
        self.assertEqual(product.price, 1000)

        # Test prix zéro (valide)
        product.price = 0
        product.save()
        self.assertEqual(product.price, 0)

    def test_order_amount_calculation(self):
        """Test de calcul des montants de commande"""
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            user_type="client",
        )

        order = Order.objects.create(
            user=user,
            payment_method="cash",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_phone="+225123456789",
            shipping_address="123 Test Street",
            shipping_city="Abidjan",
            shipping_region="Abidjan",
            shipping_country="Côte d'Ivoire",
            shipping_postal_code="12345",
            subtotal=1000,
            shipping_cost=500,
            tax_amount=150,
            total_amount=1650,
        )

        # Vérifier que le total est cohérent
        expected_total = order.subtotal + order.shipping_cost + order.tax_amount
        self.assertEqual(order.total_amount, expected_total)

    def test_user_type_validation(self):
        """Test de validation du type d'utilisateur"""
        # Test client
        client = User.objects.create_user(
            username="client",
            email="client@test.com",
            password="testpass123",
            user_type="client",
        )
        self.assertEqual(client.user_type, "client")

        # Test vendeur
        vendor = User.objects.create_user(
            username="vendor",
            email="vendor@test.com",
            password="testpass123",
            user_type="vendeur",
        )
        self.assertEqual(vendor.user_type, "vendeur")

        # Test admin
        admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            user_type="admin",
        )
        self.assertEqual(admin.user_type, "admin")
