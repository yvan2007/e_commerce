from django.contrib import admin

from .models import Wishlist, WishlistItem, WishlistShare


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "updated_at", "get_products_count"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

    def get_products_count(self, obj):
        return obj.products.count()

    get_products_count.short_description = "Nombre de produits"


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["wishlist", "product", "added_at"]
    list_filter = ["added_at", "wishlist__user"]
    search_fields = ["wishlist__user__username", "product__name"]
    readonly_fields = ["added_at"]


@admin.register(WishlistShare)
class WishlistShareAdmin(admin.ModelAdmin):
    list_display = [
        "wishlist",
        "shared_by",
        "shared_with_email",
        "is_active",
        "created_at",
        "viewed_at",
    ]
    list_filter = ["is_active", "created_at", "viewed_at"]
    search_fields = [
        "wishlist__user__username",
        "shared_with_email",
        "shared_by__username",
    ]
    readonly_fields = ["created_at"]
