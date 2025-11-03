import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, F, IntegerField, Q, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import User
from products.models import Category, Product
from search.models import SearchHistory, SearchSuggestion


def search_products(request):
    """Vue de recherche de produits avec filtres et tri"""
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    sort_by = request.GET.get("sort", "relevance")
    page = request.GET.get("page", 1)

    # Base queryset
    products = Product.objects.filter(status="published").select_related("category")

    # Filtrage par recherche textuelle
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(category__name__icontains=query)
        ).distinct()

        # Enregistrer la recherche
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                query=query,
                results_count=products.count(),
                ip_address=request.META.get("REMOTE_ADDR"),
            )

    # Filtrage par catégorie
    if category_id:
        products = products.filter(category_id=category_id)

    # Filtrage par prix
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Tri des produits
    if sort_by == "price_low":
        products = products.order_by("price")
    elif sort_by == "price_high":
        products = products.order_by("-price")
    elif sort_by == "name":
        products = products.order_by("name")
    elif sort_by == "newest":
        products = products.order_by("-created_at")
    elif sort_by == "popularity":
        products = products.order_by("-views_count")
    elif sort_by == "rating":
        products = products.annotate(
            avg_rating=Case(
                When(reviews__isnull=False, then=F("reviews__rating")),
                default=0,
                output_field=IntegerField(),
            )
        ).order_by("-avg_rating")
    elif sort_by == "discount":
        products = products.filter(discount_percentage__gt=0).order_by(
            "-discount_percentage"
        )
    else:  # relevance par défaut
        if query:
            # Tri par pertinence (produits avec le terme dans le nom en premier)
            # Utilisation de LIKE avec COLLATE NOCASE pour SQLite
            products = products.extra(
                select={
                    "relevance": "CASE WHEN products_product.name LIKE %s COLLATE NOCASE THEN 1 ELSE 2 END"
                },
                select_params=[f"%{query}%"],
            ).order_by("relevance", "-created_at")
        else:
            products = products.order_by("-created_at")

    # Pagination
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(page)

    # Données pour les filtres
    categories = Category.objects.filter(is_active=True)

    # Suggestions de recherche
    suggestions = SearchSuggestion.objects.filter(is_active=True).order_by(
        "-popularity"
    )[:5]

    context = {
        "products": page_obj,
        "query": query,
        "categories": categories,
        "selected_category": category_id,
        "min_price": min_price,
        "max_price": max_price,
        "sort_by": sort_by,
        "suggestions": suggestions,
        "total_results": paginator.count,
    }

    return render(request, "search/results.html", context)


@require_http_methods(["GET"])
def search_suggestions(request):
    """API pour les suggestions de recherche"""
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"suggestions": []})

    # Suggestions basées sur les noms de produits
    product_suggestions = Product.objects.filter(
        name__icontains=query, status="published"
    ).values_list("name", flat=True)[:5]

    # Suggestions basées sur les catégories
    category_suggestions = Category.objects.filter(
        name__icontains=query, is_active=True
    ).values_list("name", flat=True)[:3]

    # Suggestions populaires
    popular_suggestions = (
        SearchSuggestion.objects.filter(query__icontains=query, is_active=True)
        .order_by("-popularity")
        .values_list("query", flat=True)[:3]
    )

    suggestions = list(
        set(
            list(product_suggestions)
            + list(category_suggestions)
            + list(popular_suggestions)
        )
    )[:8]

    return JsonResponse({"suggestions": suggestions})


@require_http_methods(["POST"])
@csrf_exempt
def update_search_suggestion(request):
    """Mettre à jour la popularité d'une suggestion"""
    data = json.loads(request.body)
    query = data.get("query", "").strip()

    if query:
        suggestion, created = SearchSuggestion.objects.get_or_create(
            query=query, defaults={"popularity": 1}
        )
        if not created:
            suggestion.popularity += 1
            suggestion.save()

    return JsonResponse({"status": "success"})


def advanced_search(request):
    """Page de recherche avancée"""
    categories = Category.objects.filter(is_active=True)

    # Filtres disponibles
    brands = (
        Product.objects.filter(status="published", brand__isnull=False)
        .values_list("brand", flat=True)
        .distinct()
    )

    context = {
        "categories": categories,
        "brands": brands,
    }

    return render(request, "search/advanced.html", context)
