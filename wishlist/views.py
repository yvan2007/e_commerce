from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from products.models import Product
from .models import Wishlist

@login_required
def wishlist_view(request):
    """
    Vue pour afficher la liste de souhaits de l'utilisateur
    """
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.all()
    
    context = {
        'wishlist': wishlist,
        'products': products,
    }
    
    return render(request, 'wishlist/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    """
    Vue pour ajouter un produit à la liste de souhaits
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product not in wishlist.products.all():
        wishlist.products.add(product)
        messages.success(request, f'{product.name} a été ajouté à votre liste de souhaits.')
    else:
        messages.info(request, f'{product.name} est déjà dans votre liste de souhaits.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Produit ajouté à la liste de souhaits'})
    
    return redirect('wishlist:wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    """
    Vue pour retirer un produit de la liste de souhaits
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.success(request, f'{product.name} a été retiré de votre liste de souhaits.')
    else:
        messages.info(request, f'{product.name} n\'est pas dans votre liste de souhaits.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Produit retiré de la liste de souhaits'})
    
    return redirect('wishlist:wishlist')

@login_required
def toggle_wishlist(request, product_id):
    """
    Vue pour basculer l'état d'un produit dans la liste de souhaits
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        action = 'removed'
        message = f'{product.name} a été retiré de votre liste de souhaits.'
    else:
        wishlist.products.add(product)
        action = 'added'
        message = f'{product.name} a été ajouté à votre liste de souhaits.'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'action': action,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('wishlist:wishlist')
