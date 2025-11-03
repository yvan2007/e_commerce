from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    # Avis sur les commandes
    path("order/<int:order_id>/", views.review_order, name="review_order"),
    path(
        "product/<int:order_item_id>/create/",
        views.create_product_review,
        name="create_product_review",
    ),
    path(
        "delivery/<int:order_id>/create/",
        views.create_delivery_review,
        name="create_delivery_review",
    ),
    # Avis publics
    path("product/<int:product_id>/", views.product_reviews, name="product_reviews"),
    # Gestion des avis personnels
    path("my-reviews/", views.MyReviewsView.as_view(), name="my_reviews"),
    path(
        "update/<int:pk>/",
        views.UpdateProductReviewView.as_view(),
        name="update_review",
    ),
    path("delete/<int:review_id>/", views.delete_review, name="delete_review"),
    # API
    path(
        "api/helpful/<int:review_id>/", views.mark_review_helpful, name="mark_helpful"
    ),
]
