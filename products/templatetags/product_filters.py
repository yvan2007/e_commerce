from django import template
from datetime import timedelta
from django.utils import timezone

register = template.Library()


@register.filter
def is_new_product(product):
    """
    Vérifie si un produit a été créé il y a moins de 7 jours
    """
    if not product or not hasattr(product, 'created_at'):
        return False
    
    days_old = (timezone.now() - product.created_at).days
    return days_old <= 7


@register.filter
def product_age_days(product):
    """
    Retourne l'âge du produit en jours
    """
    if not product or not hasattr(product, 'created_at'):
        return 0
    
    return (timezone.now() - product.created_at).days

