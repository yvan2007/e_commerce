from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, ListView
from django.urls import reverse_lazy, reverse

from .models import DeliveryProductReview, DeliveryReview, ReviewHelpful, ReviewResponse
from .forms import ProductReviewForm, DeliveryReviewForm, ReviewResponseForm, ReviewSearchForm
from orders.models import Order, OrderItem
from products.models import Product

@login_required
def review_order(request, order_id):
    """
    Vue pour afficher les commandes disponibles pour avis
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier que la commande est livrée
    if order.status != 'delivered':
        messages.warning(request, _('Vous ne pouvez évaluer que les commandes livrées.'))
        return redirect('orders:order_detail', order_id=order_id)
    
    # Récupérer les articles non encore évalués
    reviewed_items = DeliveryProductReview.objects.filter(
        user=request.user,
        order=order
    ).values_list('order_item_id', flat=True)
    
    unreviewed_items = order.items.exclude(id__in=reviewed_items)
    
    # Vérifier s'il y a déjà un avis de livraison
    delivery_review_exists = DeliveryReview.objects.filter(
        user=request.user,
        order=order
    ).exists()
    
    context = {
        'order': order,
        'unreviewed_items': unreviewed_items,
        'delivery_review_exists': delivery_review_exists,
    }
    
    return render(request, 'reviews/review_order.html', context)

@login_required
def create_product_review(request, order_item_id):
    """
    Vue pour créer un avis sur un produit
    """
    order_item = get_object_or_404(OrderItem, id=order_item_id, order__user=request.user)
    
    # Vérifier que l'utilisateur peut évaluer cet article
    if order_item.order.status != 'delivered':
        messages.warning(request, _('Vous ne pouvez évaluer que les commandes livrées.'))
        return redirect('orders:order_detail', order_id=order_item.order.id)
    
    # Vérifier qu'il n'y a pas déjà un avis
    if DeliveryProductReview.objects.filter(user=request.user, order_item=order_item).exists():
        messages.info(request, _('Vous avez déjà évalué ce produit.'))
        return redirect('reviews:review_order', order_id=order_item.order.id)
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = order_item.product
            review.order = order_item.order
            review.order_item = order_item
            review.save()
            
            messages.success(request, _('Votre avis a été publié avec succès !'))
            return redirect('reviews:review_order', order_id=order_item.order.id)
    else:
        form = ProductReviewForm()
    
    context = {
        'form': form,
        'order_item': order_item,
        'product': order_item.product,
    }
    
    return render(request, 'reviews/create_product_review.html', context)

@login_required
def create_delivery_review(request, order_id):
    """
    Vue pour créer un avis sur la livraison
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier que la commande est livrée
    if order.status != 'delivered':
        messages.warning(request, _('Vous ne pouvez évaluer que les commandes livrées.'))
        return redirect('orders:order_detail', order_id=order_id)
    
    # Vérifier qu'il n'y a pas déjà un avis de livraison
    if DeliveryReview.objects.filter(user=request.user, order=order).exists():
        messages.info(request, _('Vous avez déjà évalué cette livraison.'))
        return redirect('reviews:review_order', order_id=order_id)
    
    if request.method == 'POST':
        form = DeliveryReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.order = order
            review.save()
            
            messages.success(request, _('Votre avis de livraison a été publié avec succès !'))
            return redirect('reviews:review_order', order_id=order_id)
    else:
        form = DeliveryReviewForm()
    
    context = {
        'form': form,
        'order': order,
    }
    
    return render(request, 'reviews/create_delivery_review.html', context)

def product_reviews(request, product_id):
    """
    Vue pour afficher tous les avis d'un produit
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Formulaire de recherche
    search_form = ReviewSearchForm(request.GET)
    reviews = DeliveryProductReview.objects.filter(
        product=product,
        is_public=True
    ).select_related('user').order_by('-created_at')
    
    # Appliquer les filtres
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        rating_filter = search_form.cleaned_data.get('rating_filter')
        sort_by = search_form.cleaned_data.get('sort_by')
        with_images = search_form.cleaned_data.get('with_images')
        
        if query:
            reviews = reviews.filter(
                Q(title__icontains=query) | Q(comment__icontains=query)
            )
        
        if rating_filter:
            reviews = reviews.filter(rating=rating_filter)
        
        if with_images:
            reviews = reviews.filter(
                Q(image_1__isnull=False) | Q(image_2__isnull=False) | Q(image_3__isnull=False)
            )
        
        # Tri
        if sort_by == 'oldest':
            reviews = reviews.order_by('created_at')
        elif sort_by == 'highest_rating':
            reviews = reviews.order_by('-rating')
        elif sort_by == 'lowest_rating':
            reviews = reviews.order_by('rating')
        elif sort_by == 'most_helpful':
            reviews = reviews.order_by('-is_helpful')
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = reviews.aggregate(
        total_reviews=Count('id'),
        average_rating=Avg('rating'),
        five_star=Count('id', filter=Q(rating=5)),
        four_star=Count('id', filter=Q(rating=4)),
        three_star=Count('id', filter=Q(rating=3)),
        two_star=Count('id', filter=Q(rating=2)),
        one_star=Count('id', filter=Q(rating=1)),
    )
    
    context = {
        'product': product,
        'page_obj': page_obj,
        'search_form': search_form,
        'stats': stats,
    }
    
    return render(request, 'reviews/product_reviews.html', context)

@require_POST
@login_required
def mark_review_helpful(request, review_id):
    """
    API pour marquer un avis comme utile
    """
    review = get_object_or_404(DeliveryProductReview, id=review_id)
    
    # Vérifier que l'utilisateur n'a pas déjà voté
    if ReviewHelpful.objects.filter(user=request.user, review=review).exists():
        return JsonResponse({'error': _('Vous avez déjà voté pour cet avis.')}, status=400)
    
    # Créer le vote
    helpful_vote = ReviewHelpful.objects.create(
        user=request.user,
        review=review,
        is_helpful=True
    )
    
    # Mettre à jour le compteur
    review.is_helpful += 1
    review.save()
    
    return JsonResponse({
        'success': True,
        'helpful_count': review.is_helpful
    })

class MyReviewsView(LoginRequiredMixin, ListView):
    """
    Vue pour afficher les avis de l'utilisateur connecté
    """
    model = DeliveryProductReview
    template_name = 'reviews/my_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        return DeliveryProductReview.objects.filter(
            user=self.request.user
        ).select_related('product', 'order').order_by('-created_at')

class UpdateProductReviewView(LoginRequiredMixin, UpdateView):
    """
    Vue pour modifier un avis existant
    """
    model = DeliveryProductReview
    form_class = ProductReviewForm
    template_name = 'reviews/update_product_review.html'
    
    def get_queryset(self):
        return DeliveryProductReview.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse('reviews:my_reviews')
    
    def form_valid(self, form):
        messages.success(self.request, _('Votre avis a été mis à jour avec succès !'))
        return super().form_valid(form)

@login_required
def delete_review(request, review_id):
    """
    Vue pour supprimer un avis
    """
    review = get_object_or_404(DeliveryProductReview, id=review_id, user=request.user)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, _('Votre avis a été supprimé.'))
        return redirect('reviews:my_reviews')
    
    context = {'review': review}
    return render(request, 'reviews/delete_review.html', context)
