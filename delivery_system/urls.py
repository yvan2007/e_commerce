from django.urls import path

from . import views

app_name = "delivery_system"

urlpatterns = [
    # Zones de livraison
    path("zones/", views.DeliveryZoneListView.as_view(), name="delivery_zones"),
    path("zones/create/", views.create_delivery_zones, name="create_delivery_zones"),
    # Adresses de livraison
    path(
        "addresses/", views.DeliveryAddressListView.as_view(), name="delivery_addresses"
    ),
    path(
        "addresses/create/",
        views.DeliveryAddressCreateView.as_view(),
        name="delivery_address_create",
    ),
    path(
        "addresses/<int:pk>/edit/",
        views.DeliveryAddressUpdateView.as_view(),
        name="delivery_address_update",
    ),
    # APIs
    path(
        "api/calculate-fee/",
        views.calculate_delivery_fee,
        name="calculate_delivery_fee",
    ),
    # Dashboard (admin)
    path("dashboard/", views.delivery_dashboard, name="delivery_dashboard"),
]
