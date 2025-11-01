"""
Commande Django pour créer des catégories et tags pour KefyStore
"""
from django.core.management.base import BaseCommand
from products.models import Category, Tag
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Créer des catégories et tags pour le site e-commerce'

    def handle(self, *args, **options):
        self.stdout.write('Création des catégories et tags...')
        
        # Créer les catégories principales
        categories_data = [
            # Électronique
            {
                'name': 'Électronique',
                'description': 'Tous les appareils électroniques',
                'children': [
                    {'name': 'Smartphones et Tablettes', 'children': [
                        {'name': 'iPhone'},
                        {'name': 'Samsung Galaxy'},
                        {'name': 'Xiaomi'},
                        {'name': 'Tablettes'},
                        {'name': 'Accessoires mobiles'},
                    ]},
                    {'name': 'Ordinateurs', 'children': [
                        {'name': 'Laptops'},
                        {'name': 'PC de Bureau'},
                        {'name': 'Ordinateurs Portables'},
                        {'name': 'Accessoires PC'},
                    ]},
                    {'name': 'Audio', 'children': [
                        {'name': 'Écouteurs'},
                        {'name': 'Enceintes'},
                        {'name': 'Casanques'},
                        {'name': 'Microphones'},
                    ]},
                    {'name': 'TV et Home Cinéma', 'children': [
                        {'name': 'Téléviseurs'},
                        {'name': 'Projecteurs'},
                        {'name': 'Soundbars'},
                        {'name': 'Accessoires TV'},
                    ]},
                ]
            },
            
            # Mode et Vêtements
            {
                'name': 'Mode et Vêtements',
                'description': 'Vêtements et accessoires de mode',
                'children': [
                    {'name': 'Femme', 'children': [
                        {'name': 'Robes'},
                        {'name': 'Hauts et T-shirts'},
                        {'name': 'Pantalons et Jupes'},
                        {'name': 'Sacs à main'},
                        {'name': 'Chaussures femme'},
                        {'name': 'Bijoux femme'},
                    ]},
                    {'name': 'Homme', 'children': [
                        {'name': 'Chemises'},
                        {'name': 'Pantalons homme'},
                        {'name': 'T-shirts'},
                        {'name': 'Chaussures homme'},
                        {'name': 'Montres homme'},
                        {'name': 'Accessoires homme'},
                    ]},
                    {'name': 'Enfant', 'children': [
                        {'name': 'Vêtements garçon'},
                        {'name': 'Vêtements fille'},
                        {'name': 'Chaussures enfant'},
                        {'name': 'Jouets'},
                    ]},
                ]
            },
            
            # Maison et Jardin
            {
                'name': 'Maison et Jardin',
                'description': 'Tout pour votre maison et jardin',
                'children': [
                    {'name': 'Mobilier', 'children': [
                        {'name': 'Salles à manger'},
                        {'name': 'Salon et Canapés'},
                        {'name': 'Chambres à coucher'},
                        {'name': 'Bureaux'},
                        {'name': 'Rangement'},
                    ]},
                    {'name': 'Décorations', 'children': [
                        {'name': 'Tapis et Carpettes'},
                        {'name': 'Tableaux'},
                        {'name': 'Plantes décoratives'},
                        {'name': 'Luminaires'},
                    ]},
                    {'name': 'Cuisine', 'children': [
                        {'name': 'Ustensiles de cuisine'},
                        {'name': 'Appareils ménagers'},
                        {'name': 'Vaiselle'},
                        {'name': 'Arts de la table'},
                    ]},
                ]
            },
            
            # Beauté et Cosmétiques
            {
                'name': 'Beauté et Cosmétiques',
                'description': 'Produits de beauté et cosmétiques',
                'children': [
                    {'name': 'Soins visage'},
                    {'name': 'Maquillage'},
                    {'name': 'Soins cheveux'},
                    {'name': 'Parfums'},
                    {'name': 'Produits corporels'},
                    {'name': 'Beauté homme'},
                ]
            },
            
            # Sport et Loisirs
            {
                'name': 'Sport et Loisirs',
                'description': 'Équipements sportifs et loisirs',
                'children': [
                    {'name': 'Fitness', 'children': [
                        {'name': 'Matériel fitness'},
                        {'name': 'Vêtements sport'},
                        {'name': 'Accessoires fitness'},
                    ]},
                    {'name': 'Running', 'children': [
                        {'name': 'Chaussures running'},
                        {'name': 'Vêtements running'},
                    ]},
                    {'name': 'Football'},
                    {'name': 'Basketball'},
                    {'name': 'Natation'},
                    {'name': 'Cyclisme'},
                ]
            },
            
            # Automobile
            {
                'name': 'Automobile',
                'description': 'Pièces et accessoires auto',
                'children': [
                    {'name': 'Pièces auto'},
                    {'name': 'Accessoires auto'},
                    {'name': 'Jantes et Pneus'},
                    {'name': 'Équipement intérieur'},
                    {'name': 'Outils auto'},
                ]
            },
            
            # Santé et Bien-être
            {
                'name': 'Santé et Bien-être',
                'description': 'Produits pour votre santé',
                'children': [
                    {'name': 'Compléments alimentaires'},
                    {'name': 'Vitamines'},
                    {'name': 'Appareils médicaux'},
                    {'name': 'Produits naturels'},
                ]
            },
            
            # Livres et Médias
            {
                'name': 'Livres et Médias',
                'description': 'Livres, DVD et médias',
                'children': [
                    {'name': 'Livres'},
                    {'name': 'DVD et Blu-ray'},
                    {'name': 'Musique'},
                    {'name': 'Jeux vidéo'},
                ]
            },
            
            # Jouets et Jeux
            {
                'name': 'Jouets et Jeux',
                'description': 'Jouets pour enfants',
                'children': [
                    {'name': 'Jouets éducatifs'},
                    {'name': 'Peluches'},
                    {'name': 'Jeux de société'},
                    {'name': 'Puzzles'},
                    {'name': 'Véhicules miniatures'},
                ]
            },
            
            # Alimentation
            {
                'name': 'Alimentation',
                'description': 'Produits alimentaires',
                'children': [
                    {'name': 'Épicerie', 'children': [
                        {'name': 'Pâtes et Riz'},
                        {'name': 'Conserves'},
                        {'name': 'Huiles et Vinaigres'},
                    ]},
                    {'name': 'Boissons', 'children': [
                        {'name': 'Eau'},
                        {'name': 'Sodas'},
                        {'name': 'Jus'},
                    ]},
                    {'name': 'Produits frais'},
                    {'name': 'Café et Thé'},
                ]
            },
            
            # Bébé et Puericulture
            {
                'name': 'Bébé et Puériculture',
                'description': 'Tout pour bébé',
                'children': [
                    {'name': 'Poussettes'},
                    {'name': 'Sièges auto'},
                    {'name': 'Équipement bébé'},
                    {'name': 'Vêtements bébé'},
                    {'name': 'Couches et Soins'},
                ]
            },
            
            # Animaux
            {
                'name': 'Animaux',
                'description': 'Accessoires pour animaux',
                'children': [
                    {'name': 'Chiens'},
                    {'name': 'Chats'},
                    {'name': 'Oiseaux'},
                    {'name': 'Aquariophilie'},
                ]
            },
            
            # Immobilier et Décoration
            {
                'name': 'Immobilier et Décoration',
                'description': 'Produits pour la maison',
                'children': [
                    {'name': 'Peintures'},
                    {'name': 'Carrelages'},
                    {'name': 'Outillage'},
                    {'name': 'Éclairage'},
                    {'name': 'Tissus'},
                ]
            },
        ]
        
        # Créer les catégories
        created_count = 0
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data.get('description', ''),
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Catégorie créée: {category.name}')
            else:
                self.stdout.write(f'  - Catégorie existe déjà: {category.name}')
            
            # Créer les sous-catégories
            for child_data in cat_data.get('children', []):
                child, created = Category.objects.get_or_create(
                    name=child_data['name'],
                    parent=category,
                    defaults={
                        'description': child_data.get('description', ''),
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'    ✓ Sous-catégorie créée: {child.name}')
                
                # Créer les sous-sous-catégories
                for subchild_data in child_data.get('children', []):
                    subchild, created = Category.objects.get_or_create(
                        name=subchild_data['name'],
                        parent=child,
                        defaults={
                            'description': subchild_data.get('description', ''),
                            'is_active': True
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'      ✓ Sous-sous-catégorie créée: {subchild.name}')
        
        # Créer les tags
        tags_data = [
            # Tags généraux
            {'name': 'Nouveauté', 'color': '#28A745'},
            {'name': 'Populaire', 'color': '#FFC107'},
            {'name': 'Promotion', 'color': '#DC3545'},
            {'name': 'Meilleure Vente', 'color': '#17A2B8'},
            {'name': 'Soldes', 'color': '#6F42C1'},
            
            # Tags Électronique
            {'name': 'Apple', 'color': '#000000'},
            {'name': 'Samsung', 'color': '#1428A0'},
            {'name': 'Xiaomi', 'color': '#FF6900'},
            {'name': 'Huawei', 'color': '#E40E02'},
            {'name': 'Haut de Gamme', 'color': '#1A1A1A'},
            {'name': 'Budget', 'color': '#58B957'},
            
            # Tags Mode
            {'name': 'Élégant', 'color': '#FF69B4'},
            {'name': 'Casual', 'color': '#87CEEB'},
            {'name': 'Sport', 'color': '#FF6347'},
            {'name': 'Été', 'color': '#FFD700'},
            {'name': 'Hiver', 'color': '#00CED1'},
            {'name': 'Grandes Tailles', 'color': '#9370DB'},
            
            # Tags Maison
            {'name': 'Moderne', 'color': '#808080'},
            {'name': 'Classique', 'color': '#DAA520'},
            {'name': 'Minimaliste', 'color': '#E6E6FA'},
            {'name': 'Scandinave', 'color': '#98FB98'},
            
            # Tags Beauté
            {'name': 'Bio', 'color': '#90EE90'},
            {'name': 'Sans Parabène', 'color': '#00CED1'},
            {'name': 'Anti-âge', 'color': '#FF1493'},
            {'name': 'Hydratant', 'color': '#00BFFF'},
            
            # Tags Sport
            {'name': 'Running', 'color': '#FF4500'},
            {'name': 'Musculation', 'color': '#8B0000'},
            {'name': 'Outdoor', 'color': '#228B22'},
            
            # Tags Qualité
            {'name': 'Qualité Premium', 'color': '#FFD700'},
            {'name': 'Garantie', 'color': '#228B22'},
            {'name': 'Certifié', 'color': '#4169E1'},
            {'name': 'Originel', 'color': '#DC143C'},
            {'name': 'En Stock', 'color': '#32CD32'},
            
            # Tags Côte d'Ivoire
            {'name': 'Made in Côte d\'Ivoire', 'color': '#FF8C00'},
            {'name': 'Artisanal', 'color': '#8B4513'},
            {'name': 'Traditionnel', 'color': '#CD853F'},
            
            # Tags Actions
            {'name': 'Flash Sale', 'color': '#DC3545'},
            {'name': 'Black Friday', 'color': '#000000'},
            {'name': 'Livraison Gratuite', 'color': '#0066CC'},
            {'name': 'Retour Gratuit', 'color': '#28A745'},
            
            # Tags utilisation
            {'name': 'Professionnel', 'color': '#4B0082'},
            {'name': 'Maison', 'color': '#FF6347'},
            {'name': 'Bureau', 'color': '#4682B4'},
            {'name': 'Voyage', 'color': '#20B2AA'},
            
            # Tags tailles
            {'name': 'Taille Unique', 'color': '#FF69B4'},
            {'name': 'Petite Taille', 'color': '#9370DB'},
            {'name': 'Grande Taille', 'color': '#800080'},
            
            # Tags matériaux
            {'name': 'Coton', 'color': '#F0FFF0'},
            {'name': 'Cuir', 'color': '#8B4513'},
            {'name': 'Inox', 'color': '#C0C0C0'},
            {'name': 'Bois', 'color': '#D2691E'},
            
            # Tags occasion
            {'name': 'Mariage', 'color': '#FFB6C1'},
            {'name': 'Anniversaire', 'color': '#FFD700'},
            {'name': 'Noël', 'color': '#DC143C'},
            {'name': 'Fête', 'color': '#FF6347'},
            
            # Tags prix
            {'name': 'Moins de 5000 FCFA', 'color': '#90EE90'},
            {'name': '5000-15000 FCFA', 'color': '#FFD700'},
            {'name': '15000-50000 FCFA', 'color': '#FF8C00'},
            {'name': 'Plus de 50000 FCFA', 'color': '#DC3545'},
        ]
        
        tags_created_count = 0
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'color': tag_data['color']
                }
            )
            
            if created:
                tags_created_count += 1
                self.stdout.write(f'  ✓ Tag créé: {tag.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Terminé! '
                f'{created_count} catégories créées, '
                f'{tags_created_count} tags créés.'
            )
        )

