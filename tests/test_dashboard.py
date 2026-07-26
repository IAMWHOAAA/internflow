import pytest
from django.urls import reverse

from jobs.models import JobApplication


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("jobs:dashboard"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_dashboard_only_shows_owned_applications(client, user, other_user, application):
    JobApplication.objects.create(
        user=other_user,
        company="不应出现公司",
        role="秘密岗位",
    )
    client.force_login(user)

    response = client.get(reverse("jobs:dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert application.company in content
    assert "不应出现公司" not in content


@pytest.mark.django_db
def test_dashboard_searches_company_role_location_and_notes(client, user):
    JobApplication.objects.create(user=user, company="甲公司", role="后端开发", location="苏州")
    JobApplication.objects.create(user=user, company="乙公司", role="数据分析", notes="Python")
    client.force_login(user)

    response = client.get(reverse("jobs:dashboard"), {"q": "Python"})
    content = response.content.decode()

    assert "乙公司" in content
    assert "甲公司" not in content


@pytest.mark.django_db
def test_dashboard_filters_status(client, user):
    JobApplication.objects.create(
        user=user,
        company="面试公司",
        role="开发",
        status=JobApplication.Status.INTERVIEW,
    )
    JobApplication.objects.create(
        user=user,
        company="待投公司",
        role="开发",
        status=JobApplication.Status.SAVED,
    )
    client.force_login(user)

    response = client.get(
        reverse("jobs:dashboard"),
        {"status": JobApplication.Status.INTERVIEW},
    )
    content = response.content.decode()

    assert "面试公司" in content
    assert "待投公司" not in content


@pytest.mark.django_db
def test_htmx_dashboard_returns_partial(client, user):
    client.force_login(user)

    response = client.get(reverse("jobs:dashboard"), headers={"HX-Request": "true"})
    content = response.content.decode()

    assert response.status_code == 200
    assert "<html" not in content
    assert "投递进度看板" in content
