"""
Tests d'intégration pour l'application e-commerce
"""
import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User, UserProfile, VendorProfile
from notifications.models import (
    Notification,
    NotificationPreference,
    NotificationTemplate,
)
from orders.models import Cart, CartItem, Order, OrderItem
from payment_system.models import MobileMoneyAccount, PaymentMethod, PaymentTransaction
from products.models import Category, Product, ProductImage, ProductReview, Tag

User = get_user_model()


class CompleteOrderFlowTest(TestCase):
    """Tests du flux complet de commande"""

    def setUp(self):
        self.client = Client()

        # Créer un client
        self.client_user = User.objects.create_user(
            username="client",
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )
        UserProfile.objects.create(user=self.client_user)
        NotificationPreference.objects.create(user=self.client_user)

        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )
        UserProfile.objects.create(user=self.vendor_user)
        VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Test Business",
            business_description="Test business description",
            is_approved=True,
        )
        NotificationPreference.objects.create(user=self.vendor_user)

        # Créer une catégorie
        self.category = Category.objects.create(
            name="Test Category", description="Test category description"
        )

        # Créer des produits
        self.products = []
        for i in range(3):
            product = Product.objects.create(
                name=f"Test Product {i+1}",
                description=f"Test product {i+1} description",
                price=Decimal(f"{100 + i*50}.00"),
                vendor=self.vendor_user,
                category=self.category,
                stock=10,
                status="published",
            )
            self.products.append(product)

        # Créer une méthode de paiement
        self.payment_method = PaymentMethod.objects.create(
            name="Moov Money", type="mobile_money", is_active=True
        )

    def test_complete_order_flow(self):
        """Test du flux complet de commande"""
        # 1. Connexion du client
        self.client.login(username="client", password="testpass123")

        # 2. Ajouter des produits au panier
        for product in self.products:
            response = self.client.post(
                reverse("products:add_to_cart", kwargs={"product_id": product.pk}),
                {"quantity": 2},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])

        # 3. Vérifier le panier
        response = self.client.get(reverse("orders:cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product 1")
        self.assertContains(response, "Test Product 2")
        self.assertContains(response, "Test Product 3")

        # 4. Passer à la commande
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)

        # 5. Soumettre la commande
        checkout_data = {
            "shipping_address": "Test Address",
            "shipping_city": "Test City",
            "shipping_postal_code": "12345",
            "payment_method": self.payment_method.id,
            "notes": "Test notes",
        }

        response = self.client.post(reverse("orders:checkout"), checkout_data)
        self.assertEqual(
            response.status_code, 302
        )  # Redirection après création de commande

        # 6. Vérifier que la commande a été créée
        order = Order.objects.get(user=self.client_user)
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.shipping_address, "Test Address")
        self.assertEqual(order.items.count(), 3)

        # 7. Vérifier que le panier a été vidé
        cart = Cart.objects.get(user=self.client_user)
        self.assertEqual(cart.items.count(), 0)

        # 8. Vérifier que les stocks ont été mis à jour
        for product in self.products:
            product.refresh_from_db()
            self.assertEqual(product.stock, 8)  # 10 - 2

    def test_payment_flow(self):
        """Test du flux de paiement"""
        # Créer une commande
        order = Order.objects.create(
            user=self.client_user,
            status="pending",
            shipping_address="Test Address",
            total_amount=Decimal("300.00"),
        )

        # Ajouter des articles à la commande
        for product in self.products:
            OrderItem.objects.create(
                order=order, product=product, quantity=1, price=product.price
            )

        # Initier le paiement
        self.client.login(username="client", password="testpass123")
        response = self.client.post(
            reverse("payment_system:initiate_payment", kwargs={"order_id": order.id}),
            {"payment_method": self.payment_method.id},
        )

        self.assertEqual(response.status_code, 200)

        # Vérifier que la transaction de paiement a été créée
        transaction = PaymentTransaction.objects.get(order=order)
        self.assertEqual(transaction.payment_method, self.payment_method)
        self.assertEqual(transaction.amount, order.total_amount)
        self.assertEqual(transaction.status, "pending")

    def test_order_status_updates(self):
        """Test des mises à jour de statut de commande"""
        # Créer une commande
        order = Order.objects.create(
            user=self.client_user,
            status="pending",
            shipping_address="Test Address",
            total_amount=Decimal("300.00"),
        )

        # Ajouter des articles à la commande
        for product in self.products:
            OrderItem.objects.create(
                order=order, product=product, quantity=1, price=product.price
            )

        # Connexion du vendeur
        self.client.login(username="vendor", password="testpass123")

        # Confirmer la commande
        response = self.client.post(
            reverse("orders:update_status", kwargs={"pk": order.id}),
            {"status": "confirmed"},
        )
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")

        # Expédier la commande
        response = self.client.post(
            reverse("orders:update_status", kwargs={"pk": order.id}),
            {"status": "shipped", "tracking_number": "TRK123456"},
        )
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")
        self.assertEqual(order.tracking_number, "TRK123456")

        # Marquer comme livré
        response = self.client.post(
            reverse("orders:update_status", kwargs={"pk": order.id}),
            {"status": "delivered"},
        )
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, "delivered")


class ProductManagementFlowTest(TestCase):
    """Tests du flux de gestion des produits"""

    def setUp(self):
        self.client = Client()

        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )
        UserProfile.objects.create(user=self.vendor_user)
        VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Test Business",
            business_description="Test business description",
            is_approved=True,
        )

        # Créer une catégorie
        self.category = Category.objects.create(
            name="Test Category", description="Test category description"
        )

        # Créer un tag
        self.tag = Tag.objects.create(
            name="Test Tag", description="Test tag description"
        )

    def test_product_creation_flow(self):
        """Test du flux de création de produit"""
        self.client.login(username="vendor", password="testpass123")

        # Accéder à la page de création de produit
        response = self.client.get(reverse("products:product_create"))
        self.assertEqual(response.status_code, 200)

        # Créer un produit
        product_data = {
            "name": "New Test Product",
            "description": "New test product description",
            "price": "150.00",
            "category": self.category.id,
            "stock": 20,
            "status": "published",
            "tags": [self.tag.id],
        }

        response = self.client.post(reverse("products:product_create"), product_data)
        self.assertEqual(response.status_code, 302)  # Redirection après création

        # Vérifier que le produit a été créé
        product = Product.objects.get(name="New Test Product")
        self.assertEqual(product.vendor, self.vendor_user)
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.price, Decimal("150.00"))
        self.assertEqual(product.stock, 20)
        self.assertEqual(product.status, "published")
        self.assertIn(self.tag, product.tags.all())

    def test_product_update_flow(self):
        """Test du flux de mise à jour de produit"""
        # Créer un produit
        product = Product.objects.create(
            name="Test Product",
            description="Test product description",
            price=Decimal("100.00"),
            vendor=self.vendor_user,
            category=self.category,
            stock=10,
            status="published",
        )

        self.client.login(username="vendor", password="testpass123")

        # Accéder à la page de modification
        response = self.client.get(
            reverse("products:product_update", kwargs={"pk": product.pk})
        )
        self.assertEqual(response.status_code, 200)

        # Modifier le produit
        update_data = {
            "name": "Updated Test Product",
            "description": "Updated test product description",
            "price": "120.00",
            "category": self.category.id,
            "stock": 15,
            "status": "published",
        }

        response = self.client.post(
            reverse("products:product_update", kwargs={"pk": product.pk}), update_data
        )
        self.assertEqual(response.status_code, 302)

        # Vérifier que le produit a été mis à jour
        product.refresh_from_db()
        self.assertEqual(product.name, "Updated Test Product")
        self.assertEqual(product.price, Decimal("120.00"))
        self.assertEqual(product.stock, 15)

    def test_product_deletion_flow(self):
        """Test du flux de suppression de produit"""
        # Créer un produit
        product = Product.objects.create(
            name="Test Product",
            description="Test product description",
            price=Decimal("100.00"),
            vendor=self.vendor_user,
            category=self.category,
            stock=10,
            status="published",
        )

        self.client.login(username="vendor", password="testpass123")

        # Supprimer le produit
        response = self.client.post(
            reverse("products:product_delete", kwargs={"pk": product.pk})
        )
        self.assertEqual(response.status_code, 302)

        # Vérifier que le produit a été supprimé
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())


class UserManagementFlowTest(TestCase):
    """Tests du flux de gestion des utilisateurs"""

    def setUp(self):
        self.client = Client()

        # Créer un administrateur
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            user_type="admin",
            is_superuser=True,
        )
        UserProfile.objects.create(user=self.admin_user)

        # Créer un vendeur en attente d'approbation
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )
        UserProfile.objects.create(user=self.vendor_user)
        VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Test Business",
            business_description="Test business description",
            is_approved=False,
        )

    def test_vendor_approval_flow(self):
        """Test du flux d'approbation de vendeur"""
        self.client.login(username="admin", password="testpass123")

        # Accéder à la page de gestion des vendeurs
        response = self.client.get(reverse("dashboard:admin_vendors"))
        self.assertEqual(response.status_code, 200)

        # Approuver le vendeur
        response = self.client.post(
            reverse("dashboard:approve_vendor", kwargs={"pk": self.vendor_user.pk}),
            {"is_approved": True},
        )
        self.assertEqual(response.status_code, 302)

        # Vérifier que le vendeur a été approuvé
        self.vendor_user.vendor_profile.refresh_from_db()
        self.assertTrue(self.vendor_user.vendor_profile.is_approved)

    def test_user_deactivation_flow(self):
        """Test du flux de désactivation d'utilisateur"""
        self.client.login(username="admin", password="testpass123")

        # Désactiver l'utilisateur
        response = self.client.post(
            reverse("dashboard:deactivate_user", kwargs={"pk": self.vendor_user.pk}),
            {"is_active": False},
        )
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur a été désactivé
        self.vendor_user.refresh_from_db()
        self.assertFalse(self.vendor_user.is_active)


class NotificationFlowTest(TestCase):
    """Tests du flux de notifications"""

    def setUp(self):
        self.client = Client()

        # Créer un client
        self.client_user = User.objects.create_user(
            username="client",
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )
        UserProfile.objects.create(user=self.client_user)
        NotificationPreference.objects.create(user=self.client_user)

        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )
        UserProfile.objects.create(user=self.vendor_user)
        VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Test Business",
            business_description="Test business description",
            is_approved=True,
        )
        NotificationPreference.objects.create(user=self.vendor_user)

        # Créer des templates de notification
        self.order_template = NotificationTemplate.objects.create(
            name="Commande passée",
            type="email",
            trigger_type="order_placed",
            subject="Nouvelle commande #{order_id}",
            content="Une nouvelle commande a été passée.",
        )

        self.payment_template = NotificationTemplate.objects.create(
            name="Paiement réussi",
            type="email",
            trigger_type="payment_success",
            subject="Paiement confirmé #{order_id}",
            content="Votre paiement a été confirmé.",
        )

    def test_order_notification_flow(self):
        """Test du flux de notification de commande"""
        # Créer une commande
        order = Order.objects.create(
            user=self.client_user,
            status="pending",
            shipping_address="Test Address",
            total_amount=Decimal("200.00"),
        )

        # Simuler l'envoi de notification
        from notifications.services import NotificationService

        success = NotificationService.send_order_notification(order, "order_placed")
        self.assertTrue(success)

        # Vérifier que la notification a été créée
        notification = Notification.objects.get(user=self.client_user)
        self.assertEqual(notification.template, self.order_template)
        self.assertEqual(notification.status, "sent")

    def test_payment_notification_flow(self):
        """Test du flux de notification de paiement"""
        # Créer une commande
        order = Order.objects.create(
            user=self.client_user,
            status="pending",
            shipping_address="Test Address",
            total_amount=Decimal("200.00"),
        )

        # Simuler l'envoi de notification
        from notifications.services import NotificationService

        success = NotificationService.send_order_notification(order, "payment_success")
        self.assertTrue(success)

        # Vérifier que la notification a été créée
        notification = Notification.objects.get(user=self.client_user)
        self.assertEqual(notification.template, self.payment_template)
        self.assertEqual(notification.status, "sent")


class SearchAndFilterFlowTest(TestCase):
    """Tests du flux de recherche et filtrage"""

    def setUp(self):
        self.client = Client()

        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )
        UserProfile.objects.create(user=self.vendor_user)
        VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Test Business",
            business_description="Test business description",
            is_approved=True,
        )

        # Créer des catégories
        self.categories = []
        for i in range(3):
            category = Category.objects.create(
                name=f"Category {i+1}", description=f"Category {i+1} description"
            )
            self.categories.append(category)

        # Créer des produits
        self.products = []
        for i in range(10):
            product = Product.objects.create(
                name=f"Product {i+1}",
                description=f"Product {i+1} description",
                price=Decimal(f"{50 + i*10}.00"),
                vendor=self.vendor_user,
                category=self.categories[i % 3],
                stock=10,
                status="published",
            )
            self.products.append(product)

    def test_search_flow(self):
        """Test du flux de recherche"""
        # Recherche simple
        response = self.client.get(reverse("search:search"), {"q": "Product 1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")

        # Recherche avec filtres
        response = self.client.get(
            reverse("search:search"),
            {
                "q": "Product",
                "category": self.categories[0].id,
                "min_price": 60,
                "max_price": 80,
            },
        )
        self.assertEqual(response.status_code, 200)

        # Recherche vide
        response = self.client.get(reverse("search:search"), {"q": "NonExistent"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucun produit trouvé")

    def test_filter_flow(self):
        """Test du flux de filtrage"""
        # Filtrer par catégorie
        response = self.client.get(
            reverse("products:product_list"), {"category": self.categories[0].id}
        )
        self.assertEqual(response.status_code, 200)

        # Filtrer par prix
        response = self.client.get(
            reverse("products:product_list"), {"min_price": 60, "max_price": 80}
        )
        self.assertEqual(response.status_code, 200)

        # Filtrer par vendeur
        response = self.client.get(
            reverse("products:product_list"), {"vendor": self.vendor_user.id}
        )
        self.assertEqual(response.status_code, 200)

    def test_sorting_flow(self):
        """Test du flux de tri"""
        # Trier par prix croissant
        response = self.client.get(reverse("products:product_list"), {"sort": "price"})
        self.assertEqual(response.status_code, 200)

        # Trier par prix décroissant
        response = self.client.get(reverse("products:product_list"), {"sort": "-price"})
        self.assertEqual(response.status_code, 200)

        # Trier par nom
        response = self.client.get(reverse("products:product_list"), {"sort": "name"})
        self.assertEqual(response.status_code, 200)

        # Trier par date de création
        response = self.client.get(
            reverse("products:product_list"), {"sort": "-created_at"}
        )
        self.assertEqual(response.status_code, 200)


class WishlistAndComparisonFlowTest(TestCase):
    """Tests du flux de wishlist et comparaison"""

    def setUp(self):
        self.client = Client()

        # Créer un client
        self.client_user = User.objects.create_user(
            username="client",
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )
        UserProfile.objects.create(user=self.client_user)

        # Créer un vendeur
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpass123",
            user_type="vendeur",
        )
        UserProfile.objects.create(user=self.vendor_user)
        VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Test Business",
            business_description="Test business description",
            is_approved=True,
        )

        # Créer une catégorie
        self.category = Category.objects.create(
            name="Test Category", description="Test category description"
        )

        # Créer des produits
        self.products = []
        for i in range(5):
            product = Product.objects.create(
                name=f"Product {i+1}",
                description=f"Product {i+1} description",
                price=Decimal(f"{100 + i*50}.00"),
                vendor=self.vendor_user,
                category=self.category,
                stock=10,
                status="published",
            )
            self.products.append(product)

    def test_wishlist_flow(self):
        """Test du flux de wishlist"""
        self.client.login(username="client", password="testpass123")

        # Ajouter des produits à la wishlist
        for product in self.products[:3]:
            response = self.client.post(
                reverse("wishlist:add_to_wishlist", kwargs={"product_id": product.pk}),
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])

        # Vérifier la wishlist
        response = self.client.get(reverse("wishlist:wishlist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")
        self.assertContains(response, "Product 2")
        self.assertContains(response, "Product 3")

        # Supprimer un produit de la wishlist
        response = self.client.post(
            reverse(
                "wishlist:remove_from_wishlist",
                kwargs={"product_id": self.products[0].pk},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

    def test_comparison_flow(self):
        """Test du flux de comparaison"""
        self.client.login(username="client", password="testpass123")

        # Ajouter des produits à la comparaison
        for product in self.products[:4]:  # Maximum 4 produits
            response = self.client.post(
                reverse(
                    "comparison:add_to_comparison", kwargs={"product_id": product.pk}
                ),
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])

        # Vérifier la page de comparaison
        response = self.client.get(reverse("comparison:comparison_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")
        self.assertContains(response, "Product 2")
        self.assertContains(response, "Product 3")
        self.assertContains(response, "Product 4")

        # Supprimer un produit de la comparaison
        response = self.client.post(
            reverse(
                "comparison:remove_from_comparison",
                kwargs={"product_id": self.products[0].pk},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Vider la comparaison
        response = self.client.post(
            reverse("comparison:clear_comparison"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
