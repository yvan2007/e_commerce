"""
Configuration de l'administration pour les analytics
"""
from django.contrib import admin
from .models import (
    AnalyticsEvent, SalesReport, ProductAnalytics, CustomerAnalytics,
    GoogleAnalytics, DashboardWidget, ReportTemplate
)


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'page_url', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'page_url', 'search_query']


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'period', 'total_orders', 'total_revenue', 'generated_at']
    list_filter = ['period', 'generated_at', 'is_public']
    search_fields = ['title', 'description']


@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['product', 'total_views', 'purchase_count', 'conversion_rate', 'revenue']
    list_filter = ['last_updated']
    search_fields = ['product__name']


@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_orders', 'total_spent', 'customer_segment', 'last_updated']
    list_filter = ['customer_segment', 'last_updated']
    search_fields = ['user__username', 'user__email']


@admin.register(GoogleAnalytics)
class GoogleAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['property_name', 'property_id', 'is_active', 'last_sync']
    list_filter = ['is_active', 'last_sync']


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'title', 'is_active', 'is_public']
    list_filter = ['widget_type', 'is_active', 'is_public']


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'format', 'is_active', 'is_public']
    list_filter = ['report_type', 'format', 'is_active', 'is_public']
    search_fields = ['name', 'description']