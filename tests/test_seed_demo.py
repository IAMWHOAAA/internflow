import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from jobs.models import InterviewPrepItem, JobApplication, ResumeProfile, StatusChange


@pytest.mark.django_db
def test_seed_demo_is_idempotent(capsys, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    call_command("seed_demo")
    first_output = capsys.readouterr().out
    call_command("seed_demo")
    second_output = capsys.readouterr().out

    user = User.objects.get(username="demo")
    assert user.check_password("internflow-demo-2026")
    assert JobApplication.objects.filter(user=user).count() == 6
    assert StatusChange.objects.filter(application__user=user).count() == 6
    assert "Username: demo" in first_output
    assert "already existed" in second_output
    assert JobApplication.objects.get(company="云帆网络").interview_at is not None
    resume = ResumeProfile.objects.get(user=user)
    assert resume.analysis["score"] >= 70
    assert resume.file.name.endswith(".docx")
    assert InterviewPrepItem.objects.filter(application__user=user).count() >= 6
