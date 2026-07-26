import pytest
from django.urls import reverse

from jobs.models import JobApplication, StatusChange


@pytest.mark.django_db
def test_application_string_and_absolute_url(application):
    assert str(application) == "星河科技 · Python 开发实习生"
    assert application.get_absolute_url() == reverse("jobs:detail", args=[application.pk])


@pytest.mark.django_db
def test_deleting_application_deletes_status_history(application):
    StatusChange.objects.create(
        application=application,
        from_status=JobApplication.Status.SAVED,
        to_status=JobApplication.Status.APPLIED,
    )

    application.delete()

    assert StatusChange.objects.count() == 0
