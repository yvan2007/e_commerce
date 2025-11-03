from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("<uuid:notification_id>/read/", views.mark_as_read, name="mark_as_read"),
    path("mark-all-read/", views.mark_all_as_read, name="mark_all_read"),
    path("<uuid:notification_id>/delete/", views.delete_notification, name="delete"),
    path(
        "delete-selected/", views.delete_selected_notifications, name="delete_selected"
    ),
    path("delete-all/", views.delete_all_notifications, name="delete_all"),
]
