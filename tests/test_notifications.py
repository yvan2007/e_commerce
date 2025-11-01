"""
Tests pour les services de notification
"""
import pytest
from django.test import TestCase
from django.core.mail import outbox
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, VendorProfile
from products.models import Category, Product
from orders.models import Order, OrderItem, Cart, CartItem
from notifications.services import (
    send_order_confirmation_email,
    send_order_status_update_email,
    send_delivery_confirmation_email,
    send_welcome_email,
    send_password_reset_email,
    send_vendor_notification_email
)

User = get_user_model()


class NotificationServiceTest(TestCase):
    """Tests pour les services de notification"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer un utilisateur client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='clientpass123',
            user_type='client',
            first_name='Test',
            last_name='Client'
        )
        
        # Créer un vendeur
        self.vendor = User.objects.create_user(
            username='vendor',
            email='vendor@example.com',
            password='vendorpass123',
            user_type='vendeur',
            first_name='Test',
            last_name='Vendor'
        )
        
        # Créer une catégorie
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test category description'
        )
        
        # Créer un produit
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            sku='TEST001',
            description='Test product description',
            vendor=self.vendor,
            category=self.category,
            price=10000,
            stock=10,
            status='active'
        )
        
        # Créer une commande
        self.order = Order.objects.create(
            user=self.client_user,
            shipping_first_name='Test',
            shipping_last_name='Client',
            shipping_phone='+22512345678',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash_on_delivery',
            subtotal=20000,
            shipping_cost=0,
            tax_amount=0,
            total_amount=20000
        )
        
        # Créer un article de commande
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=10000,
            total_price=20000
        )
    
    def test_send_order_confirmation_email(self):
        """Test d'envoi d'email de confirmation de commande"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer l'email
        result = send_order_confirmation_email(self.order)
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        self.assertEqual(len(outbox), 1)
        
        # Vérifier le contenu de l'email
        email = outbox[0]
        self.assertIn('Confirmation de votre commande', email.subject)
        self.assertIn(self.order.order_number, email.subject)
        self.assertEqual(email.to, [self.client_user.email])
        self.assertIn('Test Client', email.body)
        self.assertIn('Test Product', email.body)
        self.assertIn('20000', email.body)
    
    def test_send_order_status_update_email(self):
        """Test d'envoi d'email de mise à jour de statut"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer l'email
        result = send_order_status_update_email(self.order, 'pending', 'confirmed')
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        self.assertEqual(len(outbox), 1)
        
        # Vérifier le contenu de l'email
        email = outbox[0]
        self.assertIn('Mise à jour de votre commande', email.subject)
        self.assertIn(self.order.order_number, email.subject)
        self.assertEqual(email.to, [self.client_user.email])
        self.assertIn('Test Client', email.body)
        self.assertIn('Test Product', email.body)
    
    def test_send_delivery_confirmation_email(self):
        """Test d'envoi d'email de confirmation de livraison"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer l'email
        result = send_delivery_confirmation_email(self.order)
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        self.assertEqual(len(outbox), 1)
        
        # Vérifier le contenu de l'email
        email = outbox[0]
        self.assertIn('a été livrée', email.subject)
        self.assertIn(self.order.order_number, email.subject)
        self.assertEqual(email.to, [self.client_user.email])
        self.assertIn('Test Client', email.body)
        self.assertIn('Test Product', email.body)
    
    def test_send_welcome_email(self):
        """Test d'envoi d'email de bienvenue"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer l'email
        result = send_welcome_email(self.client_user)
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        self.assertEqual(len(outbox), 1)
        
        # Vérifier le contenu de l'email
        email = outbox[0]
        self.assertIn('Bienvenue', email.subject)
        self.assertEqual(email.to, [self.client_user.email])
        self.assertIn('Test Client', email.body)
    
    def test_send_password_reset_email(self):
        """Test d'envoi d'email de réinitialisation de mot de passe"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer l'email
        reset_url = 'http://localhost:8000/accounts/password-reset/confirm/'
        result = send_password_reset_email(self.client_user, reset_url)
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        self.assertEqual(len(outbox), 1)
        
        # Vérifier le contenu de l'email
        email = outbox[0]
        self.assertIn('Réinitialisation', email.subject)
        self.assertEqual(email.to, [self.client_user.email])
        self.assertIn('Test Client', email.body)
        self.assertIn(reset_url, email.body)
    
    def test_send_vendor_notification_email(self):
        """Test d'envoi d'email de notification au vendeur"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer l'email
        result = send_vendor_notification_email(self.order, self.vendor)
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        self.assertEqual(len(outbox), 1)
        
        # Vérifier le contenu de l'email
        email = outbox[0]
        self.assertIn('Nouvelle commande', email.subject)
        self.assertIn(self.order.order_number, email.subject)
        self.assertEqual(email.to, [self.vendor.email])
        self.assertIn('Test Vendor', email.body)
        self.assertIn('Test Product', email.body)
    
    def test_email_service_error_handling(self):
        """Test de gestion des erreurs du service email"""
        # Créer une commande avec un utilisateur sans email
        user_no_email = User.objects.create_user(
            username='noemail',
            email='',
            password='testpass123',
            user_type='client'
        )
        
        order_no_email = Order.objects.create(
            user=user_no_email,
            shipping_first_name='Test',
            shipping_last_name='NoEmail',
            shipping_phone='+22512345678',
            shipping_address='123 Test Street',
            shipping_city='Abidjan',
            payment_method='cash_on_delivery',
            subtotal=10000,
            shipping_cost=0,
            tax_amount=0,
            total_amount=10000
        )
        
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Tenter d'envoyer l'email (devrait échouer silencieusement)
        result = send_order_confirmation_email(order_no_email)
        
        # Vérifier que l'email n'a pas été envoyé
        self.assertFalse(result)
        self.assertEqual(len(outbox), 0)
    
    def test_email_template_rendering(self):
        """Test du rendu des templates d'email"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer un email de confirmation
        send_order_confirmation_email(self.order)
        
        # Vérifier que l'email contient du HTML
        email = outbox[0]
        self.assertIn('text/html', email.alternatives[0][1])
        self.assertIn('<html', email.alternatives[0][1])
        self.assertIn('</html>', email.alternatives[0][1])
    
    def test_email_attachment_handling(self):
        """Test de gestion des pièces jointes dans les emails"""
        # Vider la boîte aux lettres
        outbox.clear()
        
        # Envoyer un email de confirmation
        send_order_confirmation_email(self.order)
        
        # Vérifier que l'email a été envoyé
        email = outbox[0]
        self.assertEqual(len(outbox), 1)
        
        # Note: Les pièces jointes ne sont pas testées ici car elles nécessitent
        # des fichiers réels et une configuration de stockage appropriée
