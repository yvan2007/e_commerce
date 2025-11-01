from django.shortcuts import render
from django.db.models import Q, F, Count, Avg
from django.utils import timezone
from datetime import timedelta

from products.models import Product, Category
from home.models import HomePageBanner, FeaturedCategory, HomePageSection, Testimonial, SiteFeature
from orders.models import Order

def home(request):
    """Page d'accueil principale"""
    
    # Bannières actives
    banners = HomePageBanner.objects.filter(is_active=True).order_by('order')
    
    # Catégories mises en avant
    featured_categories = FeaturedCategory.objects.filter(
        is_active=True
    ).select_related('category').order_by('order')[:6]
    
    # Produits en promotion
    sale_products = Product.objects.filter(
        status='published',
        is_on_sale=True
    ).select_related('category', 'vendor').prefetch_related('images')[:8]
    
    # Meilleures ventes (basées sur les commandes)
    bestseller_products = Product.objects.filter(
        status='published'
    ).annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:8]
    
    # Nouveautés (derniers 30 jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_products = Product.objects.filter(
        status='published',
        created_at__gte=thirty_days_ago
    ).select_related('category', 'vendor').prefetch_related('images')[:8]
    
    # Produits les mieux notés
    top_rated_products = Product.objects.filter(
        status='published'
    ).annotate(
        avg_rating=Avg('reviews__rating')
    ).filter(
        avg_rating__gte=4.0
    ).order_by('-avg_rating')[:8]
    
    # Témoignages
    testimonials = Testimonial.objects.filter(
        is_active=True
    ).order_by('order')[:6]
    
    # Fonctionnalités du site
    features = SiteFeature.objects.filter(
        is_active=True
    ).order_by('order')[:4]
    
    # Statistiques pour l'admin
    stats = {}
    if request.user.is_authenticated and request.user.is_staff:
        stats = {
            'total_products': Product.objects.filter(status='published').count(),
            'total_orders': Order.objects.count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'sale_products_count': Product.objects.filter(status='published', is_on_sale=True).count(),
        }
    
    # Ajouter les variables nécessaires pour le template
    # Catégories actives qui ont des produits
    categories_with_products = Category.objects.filter(
        is_active=True,
        products__status='published'
    ).distinct()
    
    # Extraire les catégories parentes
    parent_categories = []
    for cat in categories_with_products:
        parent = cat.parent if cat.parent else cat
        if parent not in parent_categories and parent.is_active:
            parent_categories.append(parent)
    
    # Filtrer uniquement les catégories qui ont des produits
    categories_to_display = []
    for parent in parent_categories:
        # Compter les produits directs
        direct_count = Product.objects.filter(category=parent, status='published').count()
        # Compter les produits des sous-catégories
        children_count = Product.objects.filter(
            category__parent=parent, 
            status='published'
        ).count()
        total_count = direct_count + children_count
        
        # N'afficher que les catégories avec au moins un produit
        if total_count > 0:
            parent.published_products_count = total_count
            categories_to_display.append(parent)
    
    categories = list(categories_to_display)[:6]
    
    # Produits vedettes
    featured_products = Product.objects.filter(
        status='published',
        is_featured=True
    ).select_related('vendor', 'category')[:8]
    
    # Derniers produits
    latest_products = Product.objects.filter(
        status='published'
    ).select_related('vendor', 'category').order_by('-created_at')[:8]
    
    context = {
        'banners': banners,
        'featured_categories': featured_categories,
        'sale_products': sale_products,
        'bestseller_products': bestseller_products,
        'new_products': new_products,
        'top_rated_products': top_rated_products,
        'testimonials': testimonials,
        'features': features,
        'stats': stats,
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
    }
    
    return render(request, 'home/index.html', context)

def about(request):
    """Page à propos"""
    features = SiteFeature.objects.filter(is_active=True).order_by('order')
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order')
    
    context = {
        'features': features,
        'testimonials': testimonials,
    }
    
    return render(request, 'home/about.html', context)

def contact(request):
    """Page de contact"""
    return render(request, 'home/contact.html')
