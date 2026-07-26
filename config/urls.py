from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from jobs import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("app/", include("jobs.urls")),
    path("admin/", admin.site.urls),
]
