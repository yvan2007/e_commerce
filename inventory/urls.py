from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Gestion des fournisseurs
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    
    # Mouvements de stock
    path('movements/', views.StockMovementListView.as_view(), name='stock_movements'),
    
    # Alertes de stock
    path('alerts/', views.StockAlertListView.as_view(), name='stock_alerts'),
    
    # Rapports d'inventaire
    path('reports/', views.InventoryReportView.as_view(), name='inventory_report'),
    
    # Mise à jour du stock d'un produit
    path('product/<int:product_id>/update-stock/', views.ProductStockUpdateView.as_view(), name='product_stock_update'),
    
    # Export des données
    path('export/csv/', views.export_inventory_csv, name='export_csv'),
    path('export/excel/', views.export_inventory_excel, name='export_excel'),
]