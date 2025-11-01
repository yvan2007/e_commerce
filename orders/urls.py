from django.urls import path, include
from . import views
from . import api_views

app_name = 'orders'

urlpatterns = [
    # Panier et commande
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    
    # Commandes client
    path('list/', views.OrderListView.as_view(), name='order_list'),
    path('commande/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('commande/<str:order_number>/cancel/', views.OrderCancelView.as_view(), name='order_cancel'),
    
    # Adresses de livraison
    path('shipping-addresses/', views.ShippingAddressListView.as_view(), name='shipping_address_list'),
    path('shipping-addresses/create/', views.ShippingAddressCreateView.as_view(), name='shipping_address_create'),
    path('shipping-addresses/<int:pk>/edit/', views.ShippingAddressUpdateView.as_view(), name='shipping_address_update'),
    path('shipping-addresses/<int:pk>/delete/', views.ShippingAddressDeleteView.as_view(), name='shipping_address_delete'),
    
    # Vendeurs
    path('vendor/orders/', views.VendorOrderListView.as_view(), name='vendor_order_list'),
    
    # Administrateurs
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin_order_list'),
    path('admin/orders/<str:order_number>/status/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('admin/orders/statistics/', views.order_statistics, name='order_statistics'),
    
    # APIs
    path('api/calculate-delivery-fee/', api_views.calculate_delivery_fee, name='calculate_delivery_fee'),
    path('api/update-cart-totals/', api_views.update_cart_totals, name='update_cart_totals'),
    path('api/cart/<int:item_id>/update/', api_views.update_cart_item_ajax, name='update_cart_item'),
    path('api/cart/<int:item_id>/remove/', api_views.remove_cart_item_ajax, name='remove_cart_item'),
    path('api/create-order/', api_views.create_order_ajax, name='create_order_ajax'),
    path('api/commande/<str:order_number>/cancel/', api_views.cancel_order_ajax, name='cancel_order_ajax'),
    path('api/regions/', api_views.get_regions, name='get_regions'),
    path('api/regions/<int:region_id>/cities/', api_views.get_cities, name='get_cities'),
    path('api/delivery-methods/', api_views.get_country_delivery_methods, name='get_delivery_methods'),
    path('api/payment-logo/<str:method>/', api_views.get_payment_method_logo, name='get_payment_logo'),
]
