"""
URLs pour l'API REST de l'e-commerce
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"categories", views.CategoryViewSet)
router.register(r"products", views.ProductViewSet)
router.register(r"cart", views.CartViewSet)
router.register(r"orders", views.OrderViewSet)
router.register(r"shipping-addresses", views.ShippingAddressViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "dashboard/stats/", views.DashboardStatsView.as_view(), name="dashboard-stats"
    ),
    path("vendor/stats/", views.VendorStatsView.as_view(), name="vendor-stats"),
]
