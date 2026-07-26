from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("resume/", views.resume_center, name="resume"),
    path("resume/delete/", views.resume_delete, name="resume_delete"),
    path("new/", views.application_create, name="create"),
    path("<int:pk>/", views.application_detail, name="detail"),
    path("<int:pk>/edit/", views.application_edit, name="edit"),
    path("<int:pk>/delete/", views.application_delete, name="delete"),
    path("<int:pk>/status/", views.application_status_update, name="status_update"),
    path("<int:pk>/prep/", views.interview_prep, name="interview_prep"),
    path("<int:pk>/prep/refresh/", views.interview_prep_refresh, name="interview_prep_refresh"),
    path(
        "<int:pk>/prep/<int:item_pk>/toggle/",
        views.interview_prep_toggle,
        name="interview_prep_toggle",
    ),
]
