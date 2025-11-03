"""
Configuration de l'administration pour le système de livraison
"""
from django.contrib import admin

from .models import City, DeliveryAddress, DeliveryCalculation, DeliveryZone, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "region", "postal_code", "is_active"]
    list_filter = ["region", "is_active"]
    search_fields = ["name", "postal_code"]
    ordering = ["region", "name"]


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "zone_type", "delivery_fee", "estimated_days", "is_active"]
    list_filter = ["zone_type", "is_active"]
    search_fields = ["name", "description"]
    ordering = ["zone_type", "name"]


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "first_name",
        "last_name",
        "city",
        "is_default",
        "created_at",
    ]
    list_filter = ["is_default", "city", "country", "created_at"]
    search_fields = [
        "user__username",
        "first_name",
        "last_name",
        "city",
        "address_line_1",
    ]
    ordering = ["-is_default", "-created_at"]


@admin.register(DeliveryCalculation)
class DeliveryCalculationAdmin(admin.ModelAdmin):
    list_display = [
        "order",
        "zone",
        "base_fee",
        "total_delivery_fee",
        "estimated_delivery_date",
    ]
    list_filter = ["zone", "estimated_delivery_date", "created_at"]
    search_fields = ["order__order_number"]
    ordering = ["-created_at"]
