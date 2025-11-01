"""
Commande Django pour créer des produits d'exemple
"""
from django.core.management.base import BaseCommand
from products.models import Product, Category, Tag
from accounts.models import User
from decimal import Decimal
from django.utils.text import slugify
import random


class Command(BaseCommand):
    help = 'Créer des produits d\'exemple pour toutes les catégories'

    def handle(self, *args, **options):
        self.stdout.write('Création des produits d\'exemple...')
        
        # Récupérer ou créer un vendeur de test
        vendor, created = User.objects.get_or_create(
            username='vendor_test',
            defaults={
                'email': 'vendor@kefystore.com',
                'user_type': 'vendeur',
                'is_active': True
            }
        )
        if created:
            vendor.set_password('vendor123')
            vendor.save()
            self.stdout.write(f'  ✓ Vendeur de test créé: {vendor.username}')
        else:
            self.stdout.write(f'  - Vendeur existe déjà: {vendor.username}')
        
        # Produits d'exemple
        products_data = [
            # Mode Homme
            {
                'name': 'Pantalon Homme Classique Noir',
                'category': 'Pantalons homme',
                'price': Decimal('12000'),
                'stock': 50,
                'short_description': 'Pantalon homme élégant et confortable',
                'description': 'Superbe pantalon homme en coton de qualité. Design moderne et confortable pour toutes les occasions.',
                'tags': ['Casual', 'Élégant', 'En Stock'],
                'is_featured': True,
                'status': 'published'
            },
            {
                'name': 'Chemise Blanche Coton Premium',
                'category': 'Chemises',
                'price': Decimal('8000'),
                'stock': 30,
                'short_description': 'Chemise blanche en coton de qualité supérieure',
                'description': 'Chemise élégante en coton 100% premium. Coupe moderne et impeccable.',
                'tags': ['Coton', 'Qualité Premium', 'Élégant'],
                'is_featured': False,
                'status': 'published'
            },
            {
                'name': 'T-shirt Décontracté Gris',
                'category': 'T-shirts',
                'price': Decimal('3500'),
                'stock': 100,
                'short_description': 'T-shirt confortable pour la détente',
                'description': 'T-shirt en coton bio, très doux et confortable. Parfait pour les journées décontractées.',
                'tags': ['Casual', 'Bio', 'Coton'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Électronique - Smartphones
            {
                'name': 'iPhone 15 Pro 128GB',
                'category': 'iPhone',
                'price': Decimal('850000'),
                'stock': 10,
                'short_description': 'iPhone 15 Pro dernier modèle',
                'description': 'iPhone 15 Pro avec 128GB de stockage. Caméra avancée, design premium. Garantie 1 an.',
                'tags': ['Apple', 'Haut de Gamme', 'Nouveauté', 'Garantie'],
                'is_featured': True,
                'status': 'published'
            },
            {
                'name': 'Samsung Galaxy S23 Ultra 256GB',
                'category': 'Samsung Galaxy',
                'price': Decimal('720000'),
                'stock': 8,
                'short_description': 'Samsung Galaxy S23 Ultra haut de gamme',
                'description': 'Smartphone haut de gamme avec écran 6.8 pouces, caméra 200MP et processeur puissant.',
                'tags': ['Samsung', 'Haut de Gamme', 'Meilleure Vente'],
                'is_featured': True,
                'status': 'published'
            },
            {
                'name': 'Xiaomi Redmi Note 12 Pro',
                'category': 'Xiaomi',
                'price': Decimal('180000'),
                'stock': 25,
                'short_description': 'Smartphone Xiaomi Redmi performant et accessible',
                'description': 'Excellent rapport qualité-prix. Performance élevée, belle caméra et autonomie exceptionnelle.',
                'tags': ['Xiaomi', 'Budget', 'En Stock'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Mode Femme
            {
                'name': 'Robe Midi Élégante Rose',
                'category': 'Robes',
                'price': Decimal('25000'),
                'stock': 15,
                'short_description': 'Magnifique robe midi pour occasions spéciales',
                'description': 'Robe élégante rose en tissu fluide. Parfaite pour soirées et occasions spéciales.',
                'tags': ['Élégant', 'Mariage', 'Fête'],
                'is_featured': True,
                'status': 'published'
            },
            {
                'name': 'Sac à Main Tendance - Noir',
                'category': 'Sacs à main',
                'price': Decimal('28000'),
                'stock': 20,
                'short_description': 'Sac à main moderne et spacieux',
                'description': 'Sac à main en cuir véritable, design tendance et fonctionnel.',
                'tags': ['Élégant', 'Cuir', 'Moderne'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Beauty
            {
                'name': 'Crème Anti-âge Bio 50ml',
                'category': 'Soins visage',
                'price': Decimal('15000'),
                'stock': 40,
                'short_description': 'Crème anti-âge bio sans parabène',
                'description': 'Crème hydratante anti-âge à base d\'ingrédients naturels. Sans parabène ni parfums artificiels.',
                'tags': ['Bio', 'Anti-âge', 'Sans Parabène', 'Hydratant'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Maison
            {
                'name': 'Canapé 3 Places Moderne Gris',
                'category': 'Salon et Canapés',
                'price': Decimal('180000'),
                'stock': 5,
                'short_description': 'Canapé design moderne et confortable',
                'description': 'Superbe canapé 3 places en tissu haut de gamme. Confort optimal et design contemporain.',
                'tags': ['Moderne', 'Qualité Premium', 'Livraison Gratuite'],
                'is_featured': True,
                'status': 'published'
            },
            {
                'name': 'Tapis Moderne 200x300cm',
                'category': 'Tapis et Carpettes',
                'price': Decimal('45000'),
                'stock': 12,
                'short_description': 'Tapis design pour salon',
                'description': 'Tapis moderne en laine de qualité. Dimensions 200x300cm, design minimaliste.',
                'tags': ['Moderne', 'Minimaliste', 'Grandes Tailles'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Sport
            {
                'name': 'Chaussures Running Nike Air',
                'category': 'Chaussures running',
                'price': Decimal('55000'),
                'stock': 30,
                'short_description': 'Chaussures de course haut de gamme',
                'description': 'Chaussures running professionnelles. Excellent amorti et respirabilité.',
                'tags': ['Running', 'Sport', 'Haut de Gamme'],
                'is_featured': True,
                'status': 'published'
            },
            
            # Cuisine
            {
                'name': 'Set Casseroles Inox 7 Pièces',
                'category': 'Ustensiles de cuisine',
                'price': Decimal('65000'),
                'stock': 18,
                'short_description': 'Set complet de casseroles inox',
                'description': 'Set de casseroles en inox haute qualité, compatible toutes plaques de cuisson.',
                'tags': ['Inox', 'Qualité Premium', 'En Stock'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Automobile
            {
                'name': 'Kit LED Auto 12W',
                'category': 'Accessoires auto',
                'price': Decimal('8500'),
                'stock': 50,
                'short_description': 'Éclairage LED pour voiture',
                'description': 'Kit LED puissant 12W avec réflecteur. Facile à installer.',
                'tags': ['Automobile', 'Budget', 'Certifié'],
                'is_featured': False,
                'status': 'published'
            },
            
            # Alimentation
            {
                'name': 'Riz Parfumé 5kg Made in CI',
                'category': 'Pâtes et Riz',
                'price': Decimal('3500'),
                'stock': 200,
                'short_description': 'Riz local de qualité supérieure',
                'description': 'Riz parfumé de Côte d\'Ivoire. Qualité premium, 5kg.',
                'tags': ['Made in Côte d\'Ivoire', 'Bio', 'En Stock'],
                'is_featured': False,
                'status': 'published'
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for product_data in products_data:
            # Récupérer la catégorie
            try:
                category = Category.objects.get(name=product_data['category'])
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠ Catégorie non trouvée: {product_data["category"]}'
                ))
                continue
            
            # Vérifier si le produit existe déjà
            slug = slugify(product_data['name'])
            if Product.objects.filter(slug=slug).exists():
                skipped_count += 1
                continue
            
            # Créer le produit
            product = Product.objects.create(
                name=product_data['name'],
                vendor=vendor,
                category=category,
                price=product_data['price'],
                stock=product_data['stock'],
                min_stock=5,
                short_description=product_data['short_description'],
                description=product_data['description'],
                is_featured=product_data['is_featured'],
                status=product_data['status'],
                rating=Decimal(str(round(random.uniform(3.5, 5.0), 1))),
                review_count=random.randint(5, 50),
                views=random.randint(100, 500),
                sales_count=random.randint(10, 100) if product_data.get('is_featured') else random.randint(0, 30),
            )
            
            # Ajouter les tags
            for tag_name in product_data.get('tags', []):
                try:
                    tag = Tag.objects.get(name=tag_name)
                    product.tags.add(tag)
                except Tag.DoesNotExist:
                    pass
            
            created_count += 1
            self.stdout.write(f'  ✓ Produit créé: {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Terminé! '
                f'{created_count} produits créés, '
                f'{skipped_count} produits ignorés (existent déjà).'
            )
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n📊 Vous pouvez maintenant:'
            f'\n  - Accéder au site: http://127.0.0.1:8000'
            f'\n  - Voir les produits par catégorie'
            f'\n  - Se connecter comme vendeur: vendor_test / vendor123'
            f'\n  - Créer plus de produits avec le formulaire'
        ))

