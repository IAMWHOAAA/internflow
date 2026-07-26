import pytest
from django.contrib.auth.models import User

from jobs.models import JobApplication


@pytest.fixture
def user(db):
    return User.objects.create_user(username="moxia", password="safe-test-password")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="other", password="safe-test-password")


@pytest.fixture
def application(user):
    return JobApplication.objects.create(
        user=user,
        company="星河科技",
        role="Python 开发实习生",
        status=JobApplication.Status.APPLIED,
        location="南京",
    )
