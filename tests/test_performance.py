"""
Tests de performance pour l'application e-commerce
"""
import pytest
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.test.utils import override_settings
from decimal import Decimal
import json

from accounts.models import User, UserProfile, VendorProfile
from products.models import Product, Category, Tag
from orders.models import Order, OrderItem, Cart, CartItem
from payment_system.models import PaymentMethod, PaymentTransaction
from notifications.models import NotificationTemplate, Notification

User = get_user_model()


class DatabasePerformanceTest(TestCase):
    """Tests de performance de la base de données"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer des données de test
        self.create_test_data()
    
    def create_test_data(self):
        """Créer des données de test pour les tests de performance"""
        # Créer des utilisateurs
        self.users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                user_type='client'
            )
            UserProfile.objects.create(user=user)
            self.users.append(user)
        
        # Créer des vendeurs
        self.vendors = []
        for i in range(10):
            vendor = User.objects.create_user(
                username=f'vendor{i}',
                email=f'vendor{i}@example.com',
                password='testpass123',
                user_type='vendeur'
            )
            UserProfile.objects.create(user=vendor)
            VendorProfile.objects.create(
                user=vendor,
                business_name=f'Business {i}',
                business_description=f'Business {i} description',
                is_approved=True
            )
            self.vendors.append(vendor)
        
        # Créer des catégories
        self.categories = []
        for i in range(20):
            category = Category.objects.create(
                name=f'Category {i}',
                description=f'Category {i} description'
            )
            self.categories.append(category)
        
        # Créer des produits
        self.products = []
        for i in range(1000):
            product = Product.objects.create(
                name=f'Product {i}',
                description=f'Product {i} description',
                price=Decimal(f'{10 + i % 100}.00'),
                vendor=self.vendors[i % 10],
                category=self.categories[i % 20],
                stock=100,
                status='published'
            )
            self.products.append(product)
        
        # Créer des commandes
        self.orders = []
        for i in range(500):
            order = Order.objects.create(
                user=self.users[i % 100],
                status='pending',
                shipping_address=f'Address {i}',
                total_amount=Decimal(f'{50 + i % 200}.00')
            )
            self.orders.append(order)
            
            # Ajouter des articles à la commande
            for j in range(3):
                product = self.products[i % 1000]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=1,
                    price=product.price
                )
    
    def test_product_list_performance(self):
        """Test de performance de la liste des produits"""
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_list'))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 2.0)  # Moins de 2 secondes
        print(f"Product list execution time: {execution_time:.3f}s")
    
    def test_product_search_performance(self):
        """Test de performance de la recherche de produits"""
        start_time = time.time()
        
        response = self.client.get(reverse('search:search'), {'q': 'Product'})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1.0)  # Moins de 1 seconde
        print(f"Product search execution time: {execution_time:.3f}s")
    
    def test_product_detail_performance(self):
        """Test de performance de la page de détail d'un produit"""
        product = self.products[0]
        
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_detail', kwargs={'pk': product.pk}))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5)  # Moins de 0.5 seconde
        print(f"Product detail execution time: {execution_time:.3f}s")
    
    def test_category_list_performance(self):
        """Test de performance de la liste des catégories"""
        start_time = time.time()
        
        response = self.client.get(reverse('products:category_list'))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5)  # Moins de 0.5 seconde
        print(f"Category list execution time: {execution_time:.3f}s")
    
    def test_home_page_performance(self):
        """Test de performance de la page d'accueil"""
        start_time = time.time()
        
        response = self.client.get(reverse('products:home_page'))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1.0)  # Moins de 1 seconde
        print(f"Home page execution time: {execution_time:.3f}s")
    
    def test_database_queries_performance(self):
        """Test de performance des requêtes de base de données"""
        # Test avec un produit spécifique
        product = self.products[0]
        
        with self.assertNumQueries(5):  # Maximum 5 requêtes
            response = self.client.get(reverse('products:product_detail', kwargs={'pk': product.pk}))
            self.assertEqual(response.status_code, 200)
    
    def test_pagination_performance(self):
        """Test de performance de la pagination"""
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_list'), {'page': 1})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1.0)  # Moins de 1 seconde
        print(f"Pagination execution time: {execution_time:.3f}s")


class APIPerformanceTest(TestCase):
    """Tests de performance des APIs"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_data()
    
    def create_test_data(self):
        """Créer des données de test pour les tests d'API"""
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        UserProfile.objects.create(user=self.user)
        
        # Créer des produits
        self.products = []
        for i in range(100):
            product = Product.objects.create(
                name=f'Product {i}',
                description=f'Product {i} description',
                price=Decimal(f'{10 + i}.00'),
                vendor=self.user,
                category=Category.objects.create(name=f'Category {i}'),
                stock=100,
                status='published'
            )
            self.products.append(product)
    
    def test_api_product_list_performance(self):
        """Test de performance de l'API de liste des produits"""
        self.client.login(username='testuser', password='testpass123')
        
        start_time = time.time()
        
        response = self.client.get('/api/products/')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1.0)  # Moins de 1 seconde
        print(f"API product list execution time: {execution_time:.3f}s")
    
    def test_api_search_performance(self):
        """Test de performance de l'API de recherche"""
        start_time = time.time()
        
        response = self.client.get('/api/products/search/', {'q': 'Product'})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5)  # Moins de 0.5 seconde
        print(f"API search execution time: {execution_time:.3f}s")


class MemoryUsageTest(TestCase):
    """Tests d'utilisation de la mémoire"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_data()
    
    def create_test_data(self):
        """Créer des données de test pour les tests de mémoire"""
        # Créer des utilisateurs
        self.users = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                user_type='client'
            )
            UserProfile.objects.create(user=user)
            self.users.append(user)
        
        # Créer des produits
        self.products = []
        for i in range(200):
            product = Product.objects.create(
                name=f'Product {i}',
                description=f'Product {i} description',
                price=Decimal(f'{10 + i}.00'),
                vendor=self.users[i % 50],
                category=Category.objects.create(name=f'Category {i}'),
                stock=100,
                status='published'
            )
            self.products.append(product)
    
    def test_memory_usage_product_list(self):
        """Test d'utilisation de la mémoire pour la liste des produits"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        response = self.client.get(reverse('products:product_list'))
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(memory_used, 50)  # Moins de 50 MB
        print(f"Memory used for product list: {memory_used:.2f} MB")
    
    def test_memory_usage_search(self):
        """Test d'utilisation de la mémoire pour la recherche"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        response = self.client.get(reverse('search:search'), {'q': 'Product'})
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(memory_used, 30)  # Moins de 30 MB
        print(f"Memory used for search: {memory_used:.2f} MB")


class ConcurrencyTest(TestCase):
    """Tests de concurrence"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_data()
    
    def create_test_data(self):
        """Créer des données de test pour les tests de concurrence"""
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='client'
        )
        UserProfile.objects.create(user=self.user)
        
        # Créer un produit
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            price=Decimal('100.00'),
            vendor=self.user,
            category=Category.objects.create(name='Test Category'),
            stock=10,
            status='published'
        )
    
    def test_concurrent_cart_operations(self):
        """Test des opérations concurrentes sur le panier"""
        import threading
        import time
        
        results = []
        
        def add_to_cart():
            client = Client()
            client.login(username='testuser', password='testpass123')
            response = client.post(
                reverse('products:add_to_cart', kwargs={'product_id': self.product.pk}),
                {'quantity': 1},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            results.append(response.status_code)
        
        # Créer plusieurs threads pour ajouter au panier
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_to_cart)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier que toutes les opérations ont réussi
        self.assertEqual(len(results), 5)
        self.assertTrue(all(status == 200 for status in results))
    
    def test_concurrent_product_views(self):
        """Test des vues concurrentes de produits"""
        import threading
        import time
        
        results = []
        
        def view_product():
            client = Client()
            response = client.get(reverse('products:product_detail', kwargs={'pk': self.product.pk}))
            results.append(response.status_code)
        
        # Créer plusieurs threads pour voir le produit
        threads = []
        for i in range(10):
            thread = threading.Thread(target=view_product)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier que toutes les vues ont réussi
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status == 200 for status in results))


class LoadTest(TestCase):
    """Tests de charge"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_data()
    
    def create_test_data(self):
        """Créer des données de test pour les tests de charge"""
        # Créer des utilisateurs
        self.users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                user_type='client'
            )
            UserProfile.objects.create(user=user)
            self.users.append(user)
        
        # Créer des produits
        self.products = []
        for i in range(100):
            product = Product.objects.create(
                name=f'Product {i}',
                description=f'Product {i} description',
                price=Decimal(f'{10 + i}.00'),
                vendor=self.users[i % 20],
                category=Category.objects.create(name=f'Category {i}'),
                stock=100,
                status='published'
            )
            self.products.append(product)
    
    def test_load_product_list(self):
        """Test de charge pour la liste des produits"""
        start_time = time.time()
        
        # Simuler 100 requêtes
        for i in range(100):
            response = self.client.get(reverse('products:product_list'))
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        self.assertLess(avg_time, 0.5)  # Moins de 0.5 seconde en moyenne
        print(f"Average response time for product list: {avg_time:.3f}s")
    
    def test_load_search(self):
        """Test de charge pour la recherche"""
        start_time = time.time()
        
        # Simuler 50 requêtes de recherche
        for i in range(50):
            response = self.client.get(reverse('search:search'), {'q': f'Product {i % 10}'})
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 50
        
        self.assertLess(avg_time, 0.3)  # Moins de 0.3 seconde en moyenne
        print(f"Average response time for search: {avg_time:.3f}s")
    
    def test_load_home_page(self):
        """Test de charge pour la page d'accueil"""
        start_time = time.time()
        
        # Simuler 100 requêtes
        for i in range(100):
            response = self.client.get(reverse('products:home_page'))
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        self.assertLess(avg_time, 0.4)  # Moins de 0.4 seconde en moyenne
        print(f"Average response time for home page: {avg_time:.3f}s")


class CachePerformanceTest(TestCase):
    """Tests de performance du cache"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_data()
    
    def create_test_data(self):
        """Créer des données de test pour les tests de cache"""
        # Créer des produits
        self.products = []
        for i in range(50):
            product = Product.objects.create(
                name=f'Product {i}',
                description=f'Product {i} description',
                price=Decimal(f'{10 + i}.00'),
                vendor=User.objects.create_user(
                    username=f'vendor{i}',
                    email=f'vendor{i}@example.com',
                    password='testpass123',
                    user_type='vendeur'
                ),
                category=Category.objects.create(name=f'Category {i}'),
                stock=100,
                status='published'
            )
            self.products.append(product)
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    })
    def test_cache_performance(self):
        """Test de performance du cache"""
        from django.core.cache import cache
        
        # Vider le cache
        cache.clear()
        
        # Premier accès (sans cache)
        start_time = time.time()
        response = self.client.get(reverse('products:product_list'))
        first_time = time.time() - start_time
        
        # Deuxième accès (avec cache)
        start_time = time.time()
        response = self.client.get(reverse('products:product_list'))
        second_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(second_time, first_time)  # Le cache devrait être plus rapide
        print(f"First access time: {first_time:.3f}s")
        print(f"Second access time: {second_time:.3f}s")
        print(f"Cache improvement: {((first_time - second_time) / first_time) * 100:.1f}%")
