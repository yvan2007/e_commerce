from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
import json
import plotly.graph_objs as go
import plotly.express as px
import plotly.utils
import pandas as pd
from io import BytesIO
import base64
import logging

from .models import (
    GoogleAnalytics, SalesReport, ReportTemplate, ProductAnalytics,
    DashboardWidget, CustomerAnalytics, AnalyticsEvent
)
from products.models import Product, Category
from orders.models import Order, OrderItem
from accounts.models import User

logger = logging.getLogger(__name__)


@staff_member_required
def analytics_dashboard(request):
    """Tableau de bord principal des analytics"""
    
    # Période par défaut (30 derniers jours)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Récupérer les paramètres de période
    period = request.GET.get('period', '30d')
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    elif period == '1y':
        start_date = end_date - timedelta(days=365)
    
    # Métriques principales
    total_orders = Order.objects.filter(created_at__range=[start_date, end_date]).count()
    total_revenue = Order.objects.filter(
        created_at__range=[start_date, end_date],
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_customers = User.objects.filter(
        date_joined__range=[start_date, end_date]
    ).count()
    
    avg_order_value = Order.objects.filter(
        created_at__range=[start_date, end_date],
        status='completed'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Graphiques
    sales_chart = create_sales_chart(start_date, end_date)
    orders_chart = create_orders_chart(start_date, end_date)
    customers_chart = create_customers_chart(start_date, end_date)
    products_chart = create_top_products_chart(start_date, end_date)
    categories_chart = create_categories_chart(start_date, end_date)
    
    # Widgets du tableau de bord
    widgets = DashboardWidget.objects.filter(is_active=True).order_by('order')
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'sales_chart': sales_chart,
        'orders_chart': orders_chart,
        'customers_chart': customers_chart,
        'products_chart': products_chart,
        'categories_chart': categories_chart,
        'widgets': widgets,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'analytics/dashboard.html', context)


def create_sales_chart(start_date, end_date):
    """Créer le graphique des ventes"""
    try:
        # Données des ventes par jour
        sales_data = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status='completed'
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            total_sales=Sum('total_amount')
        ).order_by('day')
        
        dates = [item['day'] for item in sales_data]
        sales = [float(item['total_sales']) for item in sales_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=sales,
            mode='lines+markers',
            name='Ventes',
            line=dict(color='#007bff', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title='Évolution des Ventes',
            xaxis_title='Date',
            yaxis_title='Montant (XOF)',
            hovermode='x unified',
            height=400,
            showlegend=False
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Erreur création graphique ventes: {e}")
        return None


def create_orders_chart(start_date, end_date):
    """Créer le graphique des commandes"""
    try:
        # Données des commandes par jour
        orders_data = Order.objects.filter(
            created_at__range=[start_date, end_date]
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            total_orders=Count('id')
        ).order_by('day')
        
        dates = [item['day'] for item in orders_data]
        orders = [item['total_orders'] for item in orders_data]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates,
            y=orders,
            name='Commandes',
            marker_color='#28a745'
        ))
        
        fig.update_layout(
            title='Nombre de Commandes',
            xaxis_title='Date',
            yaxis_title='Nombre de Commandes',
            height=400,
            showlegend=False
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Erreur création graphique commandes: {e}")
        return None


def create_customers_chart(start_date, end_date):
    """Créer le graphique des clients"""
    try:
        # Données des nouveaux clients par jour
        customers_data = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).extra(
            select={'day': 'date(date_joined)'}
        ).values('day').annotate(
            new_customers=Count('id')
        ).order_by('day')
        
        dates = [item['day'] for item in customers_data]
        customers = [item['new_customers'] for item in customers_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=customers,
            mode='lines+markers',
            name='Nouveaux Clients',
            line=dict(color='#ffc107', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title='Nouveaux Clients',
            xaxis_title='Date',
            yaxis_title='Nombre de Clients',
            height=400,
            showlegend=False
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Erreur création graphique clients: {e}")
        return None


def create_top_products_chart(start_date, end_date):
    """Créer le graphique des produits les plus vendus"""
    try:
        # Top 10 des produits les plus vendus
        top_products = OrderItem.objects.filter(
            order__created_at__range=[start_date, end_date],
            order__status='completed'
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('price')
        ).order_by('-total_quantity')[:10]
        
        products = [item['product__name'][:30] + '...' if len(item['product__name']) > 30 
                   else item['product__name'] for item in top_products]
        quantities = [item['total_quantity'] for item in top_products]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quantities,
            y=products,
            orientation='h',
            marker_color='#17a2b8'
        ))
        
        fig.update_layout(
            title='Top 10 Produits les Plus Vendus',
            xaxis_title='Quantité Vendue',
            yaxis_title='Produits',
            height=500,
            showlegend=False
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Erreur création graphique produits: {e}")
        return None


def create_categories_chart(start_date, end_date):
    """Créer le graphique des catégories"""
    try:
        # Ventes par catégorie
        categories_data = OrderItem.objects.filter(
            order__created_at__range=[start_date, end_date],
            order__status='completed'
        ).values('product__category__name').annotate(
            total_revenue=Sum('price')
        ).order_by('-total_revenue')
        
        categories = [item['product__category__name'] for item in categories_data]
        revenues = [float(item['total_revenue']) for item in categories_data]
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=revenues,
            hole=0.3
        )])
        
        fig.update_layout(
            title='Répartition des Ventes par Catégorie',
            height=400,
            showlegend=True
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Erreur création graphique catégories: {e}")
        return None


@staff_member_required
def sales_report(request):
    """Rapport de ventes détaillé"""
    
    # Paramètres de filtrage
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category_id = request.GET.get('category')
    product_id = request.GET.get('product')
    
    # Période par défaut
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Conversion des dates
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Filtres
    orders_filter = Order.objects.filter(
        created_at__date__range=[start_date_obj, end_date_obj]
    )
    
    if category_id:
        orders_filter = orders_filter.filter(items__product__category_id=category_id).distinct()
    
    if product_id:
        orders_filter = orders_filter.filter(items__product_id=product_id).distinct()
    
    # Métriques
    total_orders = orders_filter.count()
    completed_orders = orders_filter.filter(status='completed').count()
    total_revenue = orders_filter.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    avg_order_value = orders_filter.filter(status='completed').aggregate(
        avg=Avg('total_amount')
    )['avg'] or 0
    
    # Données détaillées
    orders_data = orders_filter.filter(status='completed').select_related('user').prefetch_related('items')
    
    # Ventes par jour
    daily_sales = orders_filter.filter(status='completed').extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        orders_count=Count('id'),
        total_revenue=Sum('total_amount')
    ).order_by('day')
    
    # Top produits
    top_products = OrderItem.objects.filter(
        order__in=orders_filter.filter(status='completed')
    ).values(
        'product__name', 'product__sku'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-quantity_sold')[:20]
    
    # Catégories
    categories_data = OrderItem.objects.filter(
        order__in=orders_filter.filter(status='completed')
    ).values('product__category__name').annotate(
        total_revenue=Sum('price'),
        total_quantity=Sum('quantity')
    ).order_by('-total_revenue')
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'category_id': category_id,
        'product_id': product_id,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'daily_sales': daily_sales,
        'top_products': top_products,
        'categories_data': categories_data,
        'orders_data': orders_data[:50],  # Limiter à 50 commandes pour l'affichage
        'categories': Category.objects.all(),
        'products': Product.objects.all()[:100],  # Limiter pour les performances
    }
    
    return render(request, 'analytics/sales_report.html', context)


@staff_member_required
def customer_analytics(request):
    """Analytics des clients"""
    
    # Période par défaut
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Nouveaux clients
    new_customers = User.objects.filter(
        date_joined__range=[start_date, end_date]
    ).count()
    
    # Clients actifs (ayant passé au moins une commande)
    active_customers = User.objects.filter(
        orders__created_at__range=[start_date, end_date]
    ).distinct().count()
    
    # Clients VIP (commandes > 100,000 XOF)
    vip_customers = User.objects.filter(
        orders__status='completed',
        orders__created_at__range=[start_date, end_date]
    ).annotate(
        total_spent=Sum('orders__total_amount')
    ).filter(total_spent__gte=100000).count()
    
    # Taux de rétention
    total_customers = User.objects.count()
    retention_rate = (active_customers / total_customers * 100) if total_customers > 0 else 0
    
    # Analyse géographique (si vous avez des données de localisation)
    # customers_by_region = User.objects.values('profile__city').annotate(
    #     count=Count('id')
    # ).order_by('-count')
    
    # Analyse des segments de clients
    customer_segments = User.objects.annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).values('total_orders', 'total_spent').annotate(
        count=Count('id')
    )
    
    # Clients par période d'inscription
    customers_by_month = User.objects.filter(
        date_joined__range=[start_date, end_date]
    ).extra(
        select={'month': 'strftime("%Y-%m", date_joined)'}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'new_customers': new_customers,
        'active_customers': active_customers,
        'vip_customers': vip_customers,
        'retention_rate': retention_rate,
        'customer_segments': customer_segments,
        'customers_by_month': customers_by_month,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'analytics/customer_analytics.html', context)


@staff_member_required
def product_analytics(request):
    """Analytics des produits"""
    
    # Période par défaut
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Produits les plus vendus
    top_products = Product.objects.filter(
        orderitem__order__created_at__range=[start_date, end_date],
        orderitem__order__status='completed'
    ).annotate(
        total_sold=Sum('orderitem__quantity'),
        total_revenue=Sum('orderitem__price')
    ).order_by('-total_sold')[:20]
    
    # Produits les moins vendus
    low_performing_products = Product.objects.filter(
        orderitem__order__created_at__range=[start_date, end_date],
        orderitem__order__status='completed'
    ).annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__lt=5).order_by('total_sold')
    
    # Analyse des stocks
    low_stock_products = Product.objects.filter(
        stock_quantity__lt=10
    ).order_by('stock_quantity')
    
    # Performance par catégorie
    category_performance = Category.objects.annotate(
        total_products=Count('products'),
        total_sold=Sum('products__orderitem__quantity'),
        total_revenue=Sum('products__orderitem__price')
    ).order_by('-total_revenue')
    
    # Analyse des prix
    price_analysis = Product.objects.aggregate(
        avg_price=Avg('price'),
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    context = {
        'top_products': top_products,
        'low_performing_products': low_performing_products,
        'low_stock_products': low_stock_products,
        'category_performance': category_performance,
        'price_analysis': price_analysis,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'analytics/product_analytics.html', context)


@staff_member_required
def export_report_csv(request, report_type):
    """Exporter un rapport en CSV"""
    try:
        if report_type == 'sales':
            return export_sales_csv(request)
        elif report_type == 'customers':
            return export_customers_csv(request)
        elif report_type == 'products':
            return export_products_csv(request)
        else:
            return HttpResponse("Type de rapport non supporté", status=400)
    except Exception as e:
        logger.error(f"Erreur export CSV: {e}")
        return HttpResponse("Erreur lors de l'export", status=500)


def export_sales_csv(request):
    """Exporter les données de ventes en CSV"""
    # Récupérer les paramètres
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filtrer les données
    orders = Order.objects.filter(status='completed')
    if start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])
    
    # Créer le CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Commande', 'Client', 'Montant', 'Statut'])
    
    for order in orders:
        writer.writerow([
            order.created_at.strftime('%Y-%m-%d'),
            order.id,
            order.user.email,
            order.total_amount,
            order.status
        ])
    
    return response


def export_customers_csv(request):
    """Exporter les données clients en CSV"""
    customers = User.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Email', 'Date Inscription', 'Commandes', 'Total Dépensé'])
    
    for customer in customers:
        total_orders = customer.orders.count()
        total_spent = customer.orders.filter(status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        writer.writerow([
            customer.email,
            customer.date_joined.strftime('%Y-%m-%d'),
            total_orders,
            total_spent
        ])
    
    return response


def export_products_csv(request):
    """Exporter les données produits en CSV"""
    products = Product.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nom', 'SKU', 'Prix', 'Stock', 'Catégorie', 'Vendu'])
    
    for product in products:
        total_sold = product.orderitem_set.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        writer.writerow([
            product.name,
            product.sku,
            product.price,
            product.stock_quantity,
            product.category.name if product.category else '',
            total_sold
        ])
    
    return response


@staff_member_required
def export_report_excel(request, report_type):
    """Exporter un rapport en Excel"""
    try:
        if report_type == 'sales':
            return export_sales_excel(request)
        elif report_type == 'customers':
            return export_customers_excel(request)
        elif report_type == 'products':
            return export_products_excel(request)
        else:
            return HttpResponse("Type de rapport non supporté", status=400)
    except Exception as e:
        logger.error(f"Erreur export Excel: {e}")
        return HttpResponse("Erreur lors de l'export", status=500)


def export_sales_excel(request):
    """Exporter les données de ventes en Excel"""
    # Implémentation de l'export Excel
    # Utiliser openpyxl ou xlsxwriter
    pass


def export_customers_excel(request):
    """Exporter les données clients en Excel"""
    # Implémentation de l'export Excel
    pass


def export_products_excel(request):
    """Exporter les données produits en Excel"""
    # Implémentation de l'export Excel
    pass


@staff_member_required
def export_report_pdf(request, report_type):
    """Exporter un rapport en PDF"""
    try:
        if report_type == 'sales':
            return export_sales_pdf(request)
        elif report_type == 'customers':
            return export_customers_pdf(request)
        elif report_type == 'products':
            return export_products_pdf(request)
        else:
            return HttpResponse("Type de rapport non supporté", status=400)
    except Exception as e:
        logger.error(f"Erreur export PDF: {e}")
        return HttpResponse("Erreur lors de l'export", status=500)


def export_sales_pdf(request):
    """Exporter les données de ventes en PDF"""
    # Implémentation de l'export PDF
    # Utiliser reportlab
    pass


def export_customers_pdf(request):
    """Exporter les données clients en PDF"""
    # Implémentation de l'export PDF
    pass


def export_products_pdf(request):
    """Exporter les données produits en PDF"""
    # Implémentation de l'export PDF
    pass


@staff_member_required
def google_analytics_config(request):
    """Configuration Google Analytics"""
    if request.method == 'POST':
        tracking_id = request.POST.get('tracking_id')
        api_key = request.POST.get('api_key')
        
        ga_config, created = GoogleAnalytics.objects.get_or_create(
            defaults={
                'tracking_id': tracking_id,
                'api_key': api_key,
                'is_active': True
            }
        )
        
        if not created:
            ga_config.tracking_id = tracking_id
            ga_config.api_key = api_key
            ga_config.save()
        
        messages.success(request, "Configuration Google Analytics mise à jour.")
        return redirect('analytics:google_analytics_config')
    
    ga_config = GoogleAnalytics.objects.first()
    context = {
        'ga_config': ga_config,
    }
    return render(request, 'analytics/google_analytics_config.html', context)