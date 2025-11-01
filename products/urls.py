from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Pages principales
    path('', views.home_view, name='home_page'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),
    path('home/', views.home_view, name='home_page'),
    
    # Gestion des produits (vendeurs)
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('renew-stock/<int:product_id>/', views.renew_stock, name='renew_stock'),
    
    # Panier
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    
    # Avis
    path('add-review/<int:product_id>/', views.add_review, name='add_review'),
    
    # API
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    
    # Gestion des produits (vendeurs) - avec slug
    path('<slug:slug>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Détail produit - DOIT être en dernier car il capture tout
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
