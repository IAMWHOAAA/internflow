import pytest
from django.urls import reverse

from jobs.models import JobApplication


@pytest.mark.django_db
def test_create_application_assigns_owner_and_initial_history(client, user):
    client.force_login(user)

    response = client.post(
        reverse("jobs:create"),
        {
            "company": "新公司",
            "role": "Python 实习生",
            "status": JobApplication.Status.SAVED,
            "priority": JobApplication.Priority.HIGH,
            "work_mode": JobApplication.WorkMode.HYBRID,
            "location": "南京",
            "source_url": "https://example.com/jobs/1",
            "salary_text": "200 元/天",
            "deadline": "",
            "applied_at": "",
            "job_description": "参与 Django 项目开发",
            "notes": "准备项目介绍",
        },
    )

    application = JobApplication.objects.get(company="新公司")
    assert response.status_code == 302
    assert application.user == user
    assert application.status_changes.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("route_name", "method"),
    [
        ("jobs:detail", "get"),
        ("jobs:edit", "get"),
        ("jobs:delete", "get"),
        ("jobs:status_update", "post"),
    ],
)
def test_application_routes_hide_other_users_records(
    client,
    other_user,
    application,
    route_name,
    method,
):
    client.force_login(other_user)
    url = reverse(route_name, args=[application.pk])

    response = getattr(client, method)(url, {"status": JobApplication.Status.INTERVIEW})

    assert response.status_code == 404


@pytest.mark.django_db
def test_edit_application_records_status_change(client, user, application):
    client.force_login(user)

    response = client.post(
        reverse("jobs:edit", args=[application.pk]),
        {
            "company": application.company,
            "role": application.role,
            "status": JobApplication.Status.INTERVIEW,
            "priority": JobApplication.Priority.MEDIUM,
            "work_mode": JobApplication.WorkMode.ONSITE,
            "location": application.location,
            "source_url": "",
            "salary_text": "",
            "deadline": "",
            "applied_at": "",
            "job_description": "",
            "notes": "",
        },
    )

    application.refresh_from_db()
    change = application.status_changes.get()
    assert response.status_code == 302
    assert application.status == JobApplication.Status.INTERVIEW
    assert change.from_status == JobApplication.Status.APPLIED
    assert change.to_status == JobApplication.Status.INTERVIEW


@pytest.mark.django_db
def test_quick_status_update_records_history(client, user, application):
    client.force_login(user)

    response = client.post(
        reverse("jobs:status_update", args=[application.pk]),
        {"status": JobApplication.Status.OFFER},
    )

    application.refresh_from_db()
    change = application.status_changes.get()
    assert response.status_code == 302
    assert application.status == JobApplication.Status.OFFER
    assert change.from_status == JobApplication.Status.APPLIED
    assert change.to_status == JobApplication.Status.OFFER


@pytest.mark.django_db
def test_status_update_rejects_invalid_value_and_get(client, user, application):
    client.force_login(user)
    url = reverse("jobs:status_update", args=[application.pk])

    invalid_response = client.post(url, {"status": "not-a-status"})
    get_response = client.get(url)

    application.refresh_from_db()
    assert invalid_response.status_code == 400
    assert get_response.status_code == 400
    assert application.status == JobApplication.Status.APPLIED


@pytest.mark.django_db
def test_delete_application(client, user, application):
    client.force_login(user)

    response = client.post(reverse("jobs:delete", args=[application.pk]))

    assert response.status_code == 302
    assert response.url == reverse("jobs:dashboard")
    assert not JobApplication.objects.filter(pk=application.pk).exists()
