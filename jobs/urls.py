from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("new/", views.application_create, name="create"),
    path("<int:pk>/", views.application_detail, name="detail"),
    path("<int:pk>/edit/", views.application_edit, name="edit"),
    path("<int:pk>/delete/", views.application_delete, name="delete"),
    path("<int:pk>/status/", views.application_status_update, name="status_update"),
]
