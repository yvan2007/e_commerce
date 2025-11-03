"""
Configuration de l'administration pour le système de paiement
"""
from django.contrib import admin

from .models import (
    BankCard,
    MobileMoneyAccount,
    PaymentMethod,
    PaymentTransaction,
    RefundRequest,
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "is_active", "min_amount", "max_amount"]
    list_filter = ["type", "is_active"]
    search_fields = ["name", "description"]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_id",
        "order",
        "payment_method",
        "amount",
        "status",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at"]
    search_fields = ["transaction_id", "order__order_number", "external_transaction_id"]


@admin.register(MobileMoneyAccount)
class MobileMoneyAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "phone_number", "is_verified", "is_primary"]
    list_filter = ["provider", "is_verified", "is_primary"]
    search_fields = ["user__username", "phone_number"]


@admin.register(BankCard)
class BankCardAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "card_type",
        "last_four_digits",
        "is_verified",
        "is_primary",
    ]
    list_filter = ["card_type", "is_verified", "is_primary"]
    search_fields = ["user__username", "last_four_digits"]


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ["transaction", "user", "reason", "status", "created_at"]
    list_filter = ["status", "reason", "created_at"]
    search_fields = ["transaction__transaction_id", "user__username"]
