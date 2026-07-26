import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_landing_page_is_public(client):
    response = client.get(reverse("landing"))

    assert response.status_code == 200
    assert "让每一次投递" in response.content.decode()


@pytest.mark.django_db
def test_authenticated_user_skips_landing(client, user):
    client.force_login(user)

    response = client.get(reverse("landing"))

    assert response.status_code == 302
    assert response.url == reverse("jobs:dashboard")


@pytest.mark.django_db
def test_signup_creates_and_logs_in_user(client):
    response = client.post(
        reverse("signup"),
        {
            "username": "new-student",
            "email": "",
            "password1": "an-unusual-test-password-389",
            "password2": "an-unusual-test-password-389",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("jobs:dashboard")
    assert User.objects.filter(username="new-student").exists()
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_invalid_signup_shows_errors(client):
    response = client.post(
        reverse("signup"),
        {"username": "new-student", "password1": "different", "password2": "values"},
    )

    assert response.status_code == 200
    assert not User.objects.filter(username="new-student").exists()
