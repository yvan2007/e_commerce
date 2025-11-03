"""
Configuration de l'administration pour l'inventaire
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    InventoryReport,
    InventoryTransaction,
    ProductSupplier,
    StockAlert,
    StockMovement,
    Supplier,
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "contact_person",
        "email",
        "phone",
        "status",
        "rating",
        "get_total_products",
    ]
    list_filter = ["status", "country", "created_at"]
    search_fields = ["name", "contact_person", "email"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Informations générales",
            {"fields": ("name", "contact_person", "email", "phone", "status")},
        ),
        ("Adresse", {"fields": ("address", "city", "country", "tax_id")}),
        ("Informations commerciales", {"fields": ("payment_terms", "rating", "notes")}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_total_products(self, obj):
        return obj.get_total_products()

    get_total_products.short_description = "Produits"


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "alert_type",
        "priority",
        "current_stock",
        "threshold_value",
        "is_resolved",
        "created_at",
    ]
    list_filter = ["alert_type", "priority", "is_resolved", "created_at"]
    search_fields = ["product__name", "message"]
    readonly_fields = ["created_at", "updated_at", "resolved_at"]

    fieldsets = (
        (
            "Alerte",
            {
                "fields": (
                    "product",
                    "alert_type",
                    "priority",
                    "threshold_value",
                    "current_stock",
                )
            },
        ),
        ("Message", {"fields": ("message",)}),
        ("Résolution", {"fields": ("is_resolved", "resolved_at", "resolved_by")}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "resolved_by")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_id",
        "product",
        "transaction_type",
        "quantity",
        "unit_cost",
        "total_cost",
        "supplier",
        "created_at",
    ]
    list_filter = ["transaction_type", "created_at", "supplier"]
    search_fields = ["product__name", "supplier__name", "reference"]
    readonly_fields = ["transaction_id", "created_at"]

    fieldsets = (
        (
            "Transaction",
            {"fields": ("transaction_id", "product", "transaction_type", "quantity")},
        ),
        ("Coûts", {"fields": ("unit_cost", "total_cost")}),
        ("Fournisseur", {"fields": ("supplier", "reference")}),
        ("Notes", {"fields": ("notes",)}),
        (
            "Métadonnées",
            {"fields": ("created_by", "created_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "supplier",
        "supplier_sku",
        "cost_price",
        "minimum_order_quantity",
        "lead_time_days",
        "is_primary",
        "is_active",
    ]
    list_filter = ["is_primary", "is_active", "supplier"]
    search_fields = ["product__name", "supplier__name", "supplier_sku"]

    fieldsets = (
        ("Relation", {"fields": ("product", "supplier", "supplier_sku")}),
        (
            "Prix et quantités",
            {"fields": ("cost_price", "minimum_order_quantity", "lead_time_days")},
        ),
        ("Statut", {"fields": ("is_primary", "is_active")}),
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "movement_type",
        "quantity",
        "previous_stock",
        "new_stock",
        "created_by",
        "created_at",
    ]
    list_filter = ["movement_type", "created_at"]
    search_fields = ["product__name", "reference", "notes"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Mouvement", {"fields": ("product", "movement_type", "quantity")}),
        ("Stocks", {"fields": ("previous_stock", "new_stock")}),
        ("Référence", {"fields": ("reference", "notes")}),
        (
            "Métadonnées",
            {"fields": ("created_by", "created_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(InventoryReport)
class InventoryReportAdmin(admin.ModelAdmin):
    list_display = ["title", "report_type", "generated_by", "generated_at"]
    list_filter = ["report_type", "generated_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["generated_at"]

    fieldsets = (
        ("Rapport", {"fields": ("title", "description", "report_type")}),
        ("Données", {"fields": ("data",)}),
        (
            "Métadonnées",
            {"fields": ("generated_by", "generated_at"), "classes": ("collapse",)},
        ),
    )
