from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Product, Category, Tag, ProductImage, ProductVariant, ProductReview, ProductViewHistory
from .forms import (
    ProductForm, ProductImageForm, ProductVariantForm, 
    ProductSearchForm, ProductReviewForm, CategoryForm, TagForm
)
from orders.models import Cart, CartItem

User = get_user_model()


class ProductListView(ListView):
    """
    Vue pour lister les produits avec filtres et recherche
    """
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_paginate_by(self, queryset):
        """
        Détermine dynamiquement le nombre d'éléments par page selon le total
        """
        total = queryset.count()
        
        if total <= 12:
            return 6  # Petits catalogues : 6 par page
        elif total <= 24:
            return 12  # Catalogues moyens : 12 par page
        elif total <= 50:
            return 24  # Grands catalogues : 24 par page
        else:
            return 48  # Très grands catalogues : 48 par page
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='published').select_related('vendor', 'category')
        
        # Filtres
        search_query = self.request.GET.get('query')
        category_id = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        tags = self.request.GET.getlist('tags')
        sort_by = self.request.GET.get('sort_by', '-created_at')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()
        
        # Tri
        if sort_by:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True)
        context['tags'] = Tag.objects.all()
        context['featured_products'] = Product.objects.filter(
            status='published', 
            is_featured=True
        )[:8]
        
        # Informations sur la pagination dynamique
        queryset = self.get_queryset()
        total_products = queryset.count()
        context['total_products'] = total_products
        
        # Déterminer le ratio par page
        if total_products <= 12:
            context['products_per_page'] = 6
        elif total_products <= 24:
            context['products_per_page'] = 12
        elif total_products <= 50:
            context['products_per_page'] = 24
        else:
            context['products_per_page'] = 48
        
        return context


class ProductDetailView(DetailView):
    """
    Vue pour afficher les détails d'un produit
    """
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    
    def get_queryset(self):
        """
        Retourne les produits publiés pour tous les utilisateurs,
        ou tous les produits si l'utilisateur est le propriétaire ou un admin
        """
        queryset = Product.objects.all().select_related(
            'vendor', 'category'
        ).prefetch_related('images', 'variants', 'reviews__user')
        
        # Si l'utilisateur n'est pas authentifié ou n'est pas le propriétaire/admin, 
        # ne montrer que les produits publiés
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        elif not (self.request.user.is_staff or self.request.user.user_type == 'vendeur'):
            queryset = queryset.filter(status='published')
        else:
            # Pour les vendeurs et admins, permettre de voir tous les produits
            # Mais filtrer pour les autres utilisateurs dans le template si nécessaire
            pass
        
        return queryset
    
    def get_object(self, queryset=None):
        """
        Récupère l'objet et vérifie les permissions
        """
        obj = super().get_object(queryset)
        
        # Si le produit n'est pas publié, vérifier que l'utilisateur peut le voir
        if obj.status != 'published':
            user = self.request.user
            if not user.is_authenticated:
                from django.http import Http404
                raise Http404("Ce produit n'est pas disponible.")
            
            # Permettre aux admins et au propriétaire du produit de voir les brouillons/archivés
            if not (user.is_staff or (user.user_type == 'vendeur' and obj.vendor == user)):
                from django.http import Http404
                raise Http404("Ce produit n'est pas disponible.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Incrémenter les vues
        product.views += 1
        product.save(update_fields=['views'])
        
        # Produits similaires avec toutes les relations nécessaires
        # Toujours montrer uniquement les produits publiés dans les produits similaires
        similar_products = Product.objects.filter(
            category=product.category,
            status='published'
        ).exclude(id=product.id).select_related(
            'vendor', 'category'
        ).prefetch_related(
            'images', 'tags'
        )[:4]
        
        # Avis récents (basés sur les commandes livrées)
        from reviews.models import DeliveryProductReview
        recent_reviews = DeliveryProductReview.objects.filter(
            product=product,
            is_public=True
        ).select_related('user').order_by('-created_at')[:5]
        
        # Formulaire d'avis
        if self.request.user.is_authenticated:
            context['review_form'] = ProductReviewForm()
        
        context.update({
            'similar_products': similar_products,
            'recent_reviews': recent_reviews,
            'can_review': self.can_user_review(),
        })
        
        return context
    
    def can_user_review(self):
        """Vérifie si l'utilisateur peut laisser un avis (seulement s'il a reçu le produit)"""
        if not self.request.user.is_authenticated:
            return False
        
        product = self.get_object()
        
        # Le vendeur ne peut pas commenter son propre produit
        if product.vendor == self.request.user:
            return False
        
        # Vérifier si l'utilisateur a déjà reçu ce produit dans une commande livrée
        from orders.models import OrderItem
        from reviews.models import DeliveryProductReview
        
        # Chercher les commandes livrées contenant ce produit
        delivered_items = OrderItem.objects.filter(
            order__user=self.request.user,
            order__status='delivered',
            product=product
        )
        
        if not delivered_items.exists():
            return False
        
        # Vérifier si l'utilisateur a déjà laissé un avis sur ce produit
        has_reviewed = DeliveryProductReview.objects.filter(
            product=product,
            user=self.request.user
        ).exists()
        
        return not has_reviewed


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Vue pour créer un nouveau produit (vendeurs uniquement)
    """
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    
    def test_func(self):
        return self.request.user.user_type == 'vendeur'
    
    def form_valid(self, form):
        form.instance.vendor = self.request.user
        
        # TOUJOURS respecter le statut sélectionné dans le formulaire en PRIORITÉ
        selected_status = form.cleaned_data.get('status', 'draft')
        
        # Déterminer le statut en fonction du bouton cliqué
        if 'save_draft' in self.request.POST:
            form.instance.status = 'draft'
            # Garder la date programmée si elle existe
        elif 'save_archived' in self.request.POST:
            form.instance.status = 'archived'
            form.instance.scheduled_publish_at = None  # Annuler la programmation si archivé
        elif 'save_publish' in self.request.POST:
            # Si une date de publication est programmée, ne pas publier maintenant
            scheduled_date = form.cleaned_data.get('scheduled_publish_at')
            if scheduled_date:
                from django.utils import timezone
                if scheduled_date > timezone.now():
                    form.instance.status = 'draft'  # Garder en brouillon jusqu'à la date
                    form.instance.scheduled_publish_at = scheduled_date
                else:
                    form.instance.status = 'published'
                    form.instance.scheduled_publish_at = None
            else:
                # Respecter le statut sélectionné dans le formulaire
                form.instance.status = selected_status
                if selected_status == 'published':
                    form.instance.scheduled_publish_at = None
        else:
            # Par défaut, respecter le statut du formulaire
            form.instance.status = selected_status
            # Si le statut est draft ou archived, annuler la programmation
            if selected_status in ['draft', 'archived']:
                scheduled_date = form.cleaned_data.get('scheduled_publish_at')
                if scheduled_date:
                    from django.utils import timezone
                    # Si une date est programmée mais le statut est draft/archived, garder la date seulement pour draft
                    if selected_status == 'draft':
                        form.instance.scheduled_publish_at = scheduled_date
                    else:
                        form.instance.scheduled_publish_at = None
        
        # Gérer l'upload de l'image principale
        if self.request.FILES.get('main_image'):
            form.instance.main_image = self.request.FILES['main_image']
        
        # Calculer automatiquement le discount_percentage si is_on_sale
        product = form.save(commit=False)
        if product.is_on_sale and product.original_price and product.original_price > product.price:
            product.discount_percentage = round(
                ((product.original_price - product.price) / product.original_price) * 100
            )
        elif product.is_on_sale and product.compare_price and product.compare_price > product.price:
            product.discount_percentage = round(
                ((product.compare_price - product.price) / product.compare_price) * 100
            )
        
        # Vérifier si la date programmée est passée et publier automatiquement
        if product.scheduled_publish_at:
            from django.utils import timezone
            if timezone.now() >= product.scheduled_publish_at:
                product.status = 'published'
                if not product.published_at:
                    product.published_at = product.scheduled_publish_at
        
        # Sauvegarder le produit (cela créera le slug automatiquement)
        product.save()
        form.save_m2m()  # Pour les tags
        
        if product.scheduled_publish_at and product.status == 'draft':
            messages.success(self.request, _(f'Produit créé en brouillon. Il sera publié automatiquement le {product.scheduled_publish_at.strftime("%d/%m/%Y à %H:%M")}.'))
        else:
            messages.success(self.request, _('Produit créé avec succès !'))
        # Maintenant que le produit est sauvegardé, il a un slug
        return redirect('products:product_detail', slug=product.slug)


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier un produit (propriétaire uniquement)
    """
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    slug_field = 'slug'
    
    def test_func(self):
        product = self.get_object()
        return self.request.user == product.vendor or self.request.user.is_staff
    
    def form_valid(self, form):
        product = self.get_object()
        
        # TOUJOURS respecter le statut sélectionné dans le formulaire en PRIORITÉ
        selected_status = form.cleaned_data.get('status', product.status)
        
        # Déterminer le statut en fonction du bouton cliqué
        if 'save_draft' in self.request.POST:
            form.instance.status = 'draft'
            # Garder la date programmée si elle existe
        elif 'save_archived' in self.request.POST:
            form.instance.status = 'archived'
            form.instance.scheduled_publish_at = None  # Annuler la programmation si archivé
        elif 'save_publish' in self.request.POST:
            # Si une date de publication est programmée, ne pas publier maintenant
            scheduled_date = form.cleaned_data.get('scheduled_publish_at')
            if scheduled_date:
                from django.utils import timezone
                if scheduled_date > timezone.now():
                    form.instance.status = 'draft'  # Garder en brouillon jusqu'à la date
                    form.instance.scheduled_publish_at = scheduled_date
                else:
                    form.instance.status = 'published'
                    form.instance.scheduled_publish_at = None
            else:
                # Respecter le statut sélectionné dans le formulaire
                form.instance.status = selected_status
                if selected_status == 'published':
                    form.instance.scheduled_publish_at = None
        else:
            # Par défaut, respecter le statut du formulaire
            form.instance.status = selected_status
            # Si le statut est draft ou archived, gérer la programmation
            if selected_status in ['draft', 'archived']:
                scheduled_date = form.cleaned_data.get('scheduled_publish_at')
                if scheduled_date:
                    from django.utils import timezone
                    # Si une date est programmée mais le statut est draft/archived, garder la date seulement pour draft
                    if selected_status == 'draft':
                        form.instance.scheduled_publish_at = scheduled_date
                    else:
                        form.instance.scheduled_publish_at = None
                else:
                    form.instance.scheduled_publish_at = None
        
        # Gérer l'upload de l'image principale
        if self.request.FILES.get('main_image'):
            form.instance.main_image = self.request.FILES['main_image']
        
        # Calculer automatiquement le discount_percentage si is_on_sale
        product = form.save(commit=False)
        if product.is_on_sale and product.original_price and product.original_price > product.price:
            product.discount_percentage = round(
                ((product.original_price - product.price) / product.original_price) * 100
            )
        elif product.is_on_sale and product.compare_price and product.compare_price > product.price:
            product.discount_percentage = round(
                ((product.compare_price - product.price) / product.compare_price) * 100
            )
        
        # Vérifier si la date programmée est passée et publier automatiquement
        if product.scheduled_publish_at:
            from django.utils import timezone
            if timezone.now() >= product.scheduled_publish_at:
                product.status = 'published'
                if not product.published_at:
                    product.published_at = product.scheduled_publish_at
        
        product.save()
        form.save_m2m()  # Pour les tags
        
        if product.scheduled_publish_at and product.status == 'draft':
            messages.success(self.request, _(f'Produit mis à jour. Il sera publié automatiquement le {product.scheduled_publish_at.strftime("%d/%m/%Y à %H:%M")}.'))
        elif product.status == 'archived':
            messages.success(self.request, _('Produit archivé avec succès !'))
        elif product.status == 'draft':
            messages.success(self.request, _('Produit enregistré comme brouillon !'))
        else:
            messages.success(self.request, _('Produit mis à jour avec succès !'))
        return redirect(self.get_object().get_absolute_url())


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer un produit
    """
    model = Product
    slug_field = 'slug'
    success_url = reverse_lazy('dashboard:vendor_products')
    
    def test_func(self):
        product = self.get_object()
        return self.request.user == product.vendor or self.request.user.is_staff


class CategoryListView(ListView):
    """
    Vue pour lister les catégories
    Seules les catégories avec des produits publiés sont affichées
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # Récupérer les catégories avec des produits publiés (y compris les sous-catégories)
        categories_with_products = Category.objects.filter(
            is_active=True,
            products__status='published'
        ).distinct()
        
        # Extraire les catégories parentes
        parent_categories = []
        for cat in categories_with_products:
            parent = cat.parent if cat.parent else cat
            if parent not in parent_categories:
                parent_categories.append(parent)
        
        # Annoter avec le nombre de produits publiés (incluant les sous-catégories)
        queryset = Category.objects.filter(
            pk__in=[p.pk for p in parent_categories]
        ).annotate(
            direct_products_count=Count(
                'products', 
                filter=Q(products__status='published')
            ),
            children_products_count=Count(
                'children__products',
                filter=Q(children__products__status='published')
            )
        ).order_by('name')
        
        # Calculer le total pour chaque catégorie (produits directs + sous-catégories)
        # et filtrer uniquement celles qui ont au moins un produit
        categories_to_display = []
        for cat in queryset:
            cat.published_products_count = (cat.direct_products_count or 0) + (cat.children_products_count or 0)
            # Inclure uniquement les catégories qui ont au moins un produit publié
            if cat.published_products_count > 0:
                categories_to_display.append(cat)
        
        # Convertir en liste pour permettre le slice et l'itération
        # Trier par nom avant de retourner
        categories_to_display.sort(key=lambda x: x.name)
        return categories_to_display


def category_detail_view(request, slug):
    """
    Vue pour afficher les produits d'une catégorie
    """
    from django.shortcuts import get_object_or_404
    from django.core.paginator import Paginator
    
    try:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        
        # Récupérer les produits de la catégorie ET de ses sous-catégories
        from django.db.models import Q
        
        # Obtenir les IDs de toutes les sous-catégories
        subcategory_ids = [category.id]  # Commencer avec la catégorie elle-même
        subcategory_ids.extend(
            category.children.values_list('id', flat=True)
        )
        
        # Récupérer tous les produits de la catégorie et ses sous-catégories
        products = Product.objects.filter(
            category__id__in=subcategory_ids,
            status='published'
        ).select_related('vendor').prefetch_related('tags')
        
        if not products.exists():
            # Si pas de produits, rediriger vers la liste des catégories
            messages.info(request, f'La catégorie "{category.name}" ne contient aucun produit pour le moment.')
            return redirect('products:category_list')
        
        # Pagination
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'category': category,
            'products': page_obj,
            'page_obj': page_obj,
        }
        
        return render(request, 'products/category_detail.html', context)
        
    except Exception as e:
        messages.error(request, 'Erreur lors du chargement de la catégorie.')
        return redirect('products:category_list')


@login_required
def add_to_cart(request, product_id):
    """
    Vue pour ajouter un produit au panier
    """
    product = get_object_or_404(Product, id=product_id, status='published')
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        messages.error(request, _('La quantité doit être positive.'))
        return redirect('products:product_detail', slug=product.slug)
    
    if quantity > product.stock:
        messages.error(request, _('Quantité insuffisante en stock.'))
        return redirect('products:product_detail', slug=product.slug)
    
    # Récupérer ou créer le panier
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Récupérer la variante si spécifiée
    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.get(id=variant_id, product=product)
        except ProductVariant.DoesNotExist:
            messages.error(request, _('Variante invalide.'))
            return redirect('products:product_detail', slug=product.slug)
    
    # Ajouter ou mettre à jour l'article
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, _('Produit ajouté au panier avec succès.'))
    
    # Répondre en AJAX si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
        from django.http import JsonResponse
        from django.db.models import Sum
        
        # Calculer le nombre total d'articles dans le panier
        cart_items = CartItem.objects.filter(cart=cart)
        cart_count = cart_items.aggregate(total=Sum('quantity'))['total'] or 0
        cart_total_price = cart.get_total_price()
        
        return JsonResponse({
            'success': True,
            'message': _('Produit ajouté au panier avec succès.'),
            'cart_count': cart_count,
            'cart_total': float(cart_total_price),
            'product_name': product.name
        })
    
    return redirect('products:product_detail', slug=product.slug)


@login_required
def remove_from_cart(request, item_id):
    """
    Vue pour retirer un produit du panier
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    messages.success(request, _('Produit retiré du panier.'))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = request.user.cart
        return JsonResponse({
            'success': True,
            'message': _('Produit retiré du panier.'),
            'cart_count': cart.get_total_items()
        })
    
    return redirect('orders:cart')


@login_required
def update_cart_item(request, item_id):
    """
    Vue pour mettre à jour la quantité d'un article du panier
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, _('Article retiré du panier.'))
    else:
        if quantity > cart_item.product.stock:
            messages.error(request, _('Quantité insuffisante en stock.'))
            return redirect('orders:cart')
        
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, _('Quantité mise à jour.'))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = request.user.cart
        cart_items = cart.items.select_related('product').all()
        cart_total = sum(item.get_total_price() for item in cart_items)
        
        return JsonResponse({
            'success': True,
            'message': _('Panier mis à jour.'),
            'cart_count': cart.get_total_items(),
            'total_price': str(cart_item.get_total_price()),
            'cart_total': str(cart_total)
        })
    
    return redirect('orders:cart')


@login_required
def add_review(request, product_id):
    """
    Vue pour ajouter un avis sur un produit
    """
    product = get_object_or_404(Product, id=product_id, status='published')
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.is_verified_purchase = True  # À implémenter selon la logique métier
            review.save()
            
            # Mettre à jour les statistiques du produit
            product.update_rating()
            
            messages.success(request, _('Votre avis a été ajouté avec succès.'))
            return redirect('products:product_detail', slug=product.slug)
    else:
        form = ProductReviewForm()
    
    return render(request, 'products/add_review.html', {
        'form': form,
        'product': product
    })


@login_required
def view_history(request):
    """
    Vue pour afficher l'historique des produits consultés
    """
    history_items = ProductViewHistory.objects.filter(
        user=request.user
    ).select_related('product').order_by('-viewed_at')[:20]
    
    context = {
        'history_items': history_items
    }
    
    return render(request, 'products/view_history.html', context)


def home_view(request):
    """
    Vue d'accueil du site
    """
    featured_products = Product.objects.filter(
        status='published',
        is_featured=True
    ).select_related('vendor', 'category')[:8]
    
    latest_products = Product.objects.filter(
        status='published'
    ).select_related('vendor', 'category').order_by('-created_at')[:8]
    
    # Afficher uniquement les catégories qui ont des produits publiés
    # Inclure les catégories parentes et leurs sous-catégories qui ont des produits
    categories_with_products = Category.objects.filter(
        is_active=True,
        products__status='published'
    ).distinct()
    
    # Extraire les catégories parentes qui contiennent ces catégories
    parent_categories = []
    for cat in categories_with_products:
        parent = cat.parent if cat.parent else cat
        if parent not in parent_categories and parent.is_active:
            parent_categories.append(parent)
    
    categories = list(parent_categories)[:6]
    
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    
    return render(request, 'home/index.html', context)


def search_suggestions(request):
    """
    API pour les suggestions de recherche
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(short_description__icontains=query),
        status='published'
    )[:5]
    
    suggestions = [{
        'name': product.name,
        'url': product.get_absolute_url(),
        'image': product.images.first().image.url if product.images.exists() else None,
        'price': str(product.price)
    } for product in products]
    
    return JsonResponse({'suggestions': suggestions})


# Vue pour renouveler le stock d'un produit
@login_required
def renew_stock(request, product_id):
    """
    Vue pour renouveler le stock d'un produit en rupture
    """
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Vérifier que le vendeur est propriétaire du produit
        if product.vendor != request.user:
            messages.error(request, 'Vous n\'avez pas la permission de modifier ce produit.')
            return redirect('products:product_list')
        
        quantity = request.POST.get('quantity')
        
        if quantity:
            try:
                quantity = int(quantity)
                if quantity > 0:
                    # Remettre le produit en stock
                    product.set_in_stock(quantity)
                    messages.success(
                        request, 
                        f'Stock renouvelé pour "{product.name}" : {quantity} unités'
                    )
                else:
                    messages.error(request, 'La quantité doit être positive.')
            except ValueError:
                messages.error(request, 'La quantité doit être un nombre valide.')
        else:
            messages.error(request, 'Veuillez spécifier une quantité.')
    
    return redirect('products:product_list')


# Context processor pour le panier
def cart_context(request):
    """
    Context processor pour ajouter le panier à tous les templates
    """
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            cart_items = cart.items.select_related('product').all()
            cart_total = sum(item.get_total_price() for item in cart_items)
            cart_count = sum(item.quantity for item in cart_items)
        except Cart.DoesNotExist:
            cart_items = []
            cart_total = 0
            cart_count = 0
    else:
        cart_items = []
        cart_total = 0
        cart_count = 0
    
    return {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    }