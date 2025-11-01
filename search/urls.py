from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_products, name='search'),
    path('advanced/', views.advanced_search, name='advanced_search'),
    path('suggestions/', views.search_suggestions, name='suggestions'),
    path('update-suggestion/', views.update_search_suggestion, name='update_suggestion'),
]
