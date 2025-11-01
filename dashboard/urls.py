from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Tableaux de bord
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('vendor/', views.VendorDashboardView.as_view(), name='vendor_dashboard'),
    
    # Gestion des produits (vendeurs)
    path('vendor/products/', views.vendor_products, name='vendor_products'),
    path('vendor/orders/', views.vendor_orders, name='vendor_orders'),
    
    # Gestion des utilisateurs (admin)
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/<int:user_id>/toggle-status/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
    path('admin/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('admin/users/<int:user_id>/toggle-vendor-approval/', views.admin_vendor_toggle_approval, name='admin_vendor_toggle_approval'),
    path('admin/products/', views.admin_products, name='admin_products'),
    
    # Gestion des catégories (admin) - CRUD complet
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/categories/create/', views.admin_category_create, name='admin_category_create'),
    path('admin/categories/<int:category_id>/update/', views.admin_category_update, name='admin_category_update'),
    path('admin/categories/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),
    
    path('admin/reviews/', views.admin_reviews, name='admin_reviews'),
    
    # APIs
    path('api/approve-review/<int:review_id>/', views.approve_review, name='approve_review'),
    path('api/delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('api/toggle-product-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('api/toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
]
