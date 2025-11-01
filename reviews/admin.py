from django.contrib import admin
from .models import DeliveryProductReview, DeliveryReview, ReviewHelpful, ReviewResponse

@admin.register(DeliveryProductReview)
class DeliveryProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'title', 'is_public', 'created_at']
    list_filter = ['rating', 'is_public', 'is_verified_purchase', 'created_at']
    search_fields = ['user__username', 'product__name', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(DeliveryReview)
class DeliveryReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'order', 'delivery_rating', 'delivery_speed_rating', 'packaging_rating', 'delivery_person_rating', 'created_at']
    list_filter = ['delivery_rating', 'delivery_speed_rating', 'packaging_rating', 'delivery_person_rating', 'created_at']
    search_fields = ['user__username', 'order__order_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['user', 'review', 'is_helpful', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ['review', 'vendor', 'created_at']
    list_filter = ['created_at']
    search_fields = ['vendor__username', 'response_text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
