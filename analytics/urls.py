from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    # Tableau de bord principal
    path("dashboard/", views.analytics_dashboard, name="dashboard"),
    # Rapports
    path("sales-report/", views.sales_report, name="sales_report"),
    path("customer-analytics/", views.customer_analytics, name="customer_analytics"),
    path("product-analytics/", views.product_analytics, name="product_analytics"),
    # Exports
    path("export/csv/<str:report_type>/", views.export_report_csv, name="export_csv"),
    path(
        "export/excel/<str:report_type>/",
        views.export_report_excel,
        name="export_excel",
    ),
    path("export/pdf/<str:report_type>/", views.export_report_pdf, name="export_pdf"),
    # Configuration Google Analytics
    path(
        "google-analytics/",
        views.google_analytics_config,
        name="google_analytics_config",
    ),
]
