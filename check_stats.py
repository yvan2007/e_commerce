#!/usr/bin/env python
"""
Script pour vérifier les statistiques : produits et catégories actives
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_site.settings')
django.setup()

from products.models import Category, Product
from accounts.models import User
from django.db.models import Q, Count

print("\n" + "="*80)
print("📊 STATISTIQUES : PRODUITS ET CATÉGORIES")
print("="*80 + "\n")

# ============================================
# PRODUITS
# ============================================
print("📦 PRODUITS")
print("-" * 80)

# Total produits
total_products = Product.objects.count()
print(f"  Total produits: {total_products}")

# Par statut
draft_products = Product.objects.filter(status='draft').count()
published_products = Product.objects.filter(status='published').count()
archived_products = Product.objects.filter(status='archived').count()

print(f"    ├─ Brouillons (draft): {draft_products}")
print(f"    ├─ Publiés (published): {published_products}")
print(f"    └─ Archivés (archived): {archived_products}")

# Par vendeur
products_by_vendor = Product.objects.values('vendor__username').annotate(
    count=Count('id')
).order_by('-count')

print(f"\n  Produits par vendeur:")
for item in products_by_vendor:
    vendor_name = item['vendor__username']
    count = item['count']
    print(f"    → {vendor_name}: {count} produit(s)")

# Produits avec/sans stock
in_stock = Product.objects.filter(stock__gt=0).count()
out_of_stock = Product.objects.filter(stock=0).count()

print(f"\n  Stock:")
print(f"    ├─ En stock: {in_stock}")
print(f"    └─ Rupture de stock: {out_of_stock}")

print()

# ============================================
# CATÉGORIES
# ============================================
print("📁 CATÉGORIES")
print("-" * 80)

# Total catégories
total_categories = Category.objects.count()
active_categories = Category.objects.filter(is_active=True).count()
inactive_categories = Category.objects.filter(is_active=False).count()

print(f"  Total catégories: {total_categories}")
print(f"    ├─ Actives: {active_categories}")
print(f"    └─ Inactives: {inactive_categories}")

# Catégories parentes vs sous-catégories
parent_categories = Category.objects.filter(parent__isnull=True).count()
subcategories = Category.objects.filter(parent__isnull=False).count()

print(f"\n  Structure:")
print(f"    ├─ Catégories parentes: {parent_categories}")
print(f"    └─ Sous-catégories: {subcategories}")

# Catégories avec/sans produits publiés
# Utiliser le comptage direct pour éviter les problèmes d'annotation
categories_all = Category.objects.filter(is_active=True).select_related('parent')

categories_with = []
categories_without = []

for cat in categories_all:
    # Comptage direct (plus fiable que l'annotation)
    direct_count = Product.objects.filter(category=cat, status='published').count()
    children_count = Product.objects.filter(
        category__parent=cat,
        status='published'
    ).count()
    total = direct_count + children_count
    
    if total > 0:
        categories_with.append((cat.name, total, cat.parent is None))
    else:
        categories_without.append((cat.name, cat.parent is None))

print(f"\n  Catégories actives avec produits publiés: {len(categories_with)}")
print("    Liste:")
for name, count, is_parent in categories_with:
    parent_label = "(PARENTE)" if is_parent else "(SOUS-CATÉGORIE)"
    print(f"      → {name} {parent_label}: {count} produit(s)")

print(f"\n  Catégories actives SANS produits: {len(categories_without)}")
if len(categories_without) > 0:
    print("    Liste (premières 10):")
    for name, is_parent in categories_without[:10]:
        parent_label = "(PARENTE)" if is_parent else "(SOUS-CATÉGORIE)"
        print(f"      → {name} {parent_label}")
    if len(categories_without) > 10:
        print(f"      ... et {len(categories_without) - 10} autres")

# Catégories visibles sur le site
from products.context_processors import categories

class MockRequest:
    pass

request = MockRequest()
context = categories(request)
visible_categories = context.get('categories', [])

print(f"\n  🌐 Catégories VISIBLES sur le site: {len(visible_categories)}")
for cat in visible_categories:
    count = getattr(cat, 'published_products_count', 0)
    print(f"    → {cat.name}: {count} produit(s)")

print()

# ============================================
# RÉSUMÉ
# ============================================
print("="*80)
print("📋 RÉSUMÉ")
print("="*80)
print()
print(f"✅ Produits publiés: {published_products}")
print(f"✅ Catégories actives: {active_categories}")
print(f"✅ Catégories avec produits: {len(categories_with)}")
print(f"✅ Catégories visibles sur le site: {len(visible_categories)}")
print(f"❌ Catégories vides (non visibles): {len(categories_without)}")
print()

