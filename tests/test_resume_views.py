from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from docx import Document

from jobs.models import InterviewPrepItem, JobApplication, ResumeProfile


def resume_docx(text: str) -> SimpleUploadedFile:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return SimpleUploadedFile(
        "我的简历.docx",
        output.getvalue(),
        content_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    )


def create_resume(user) -> ResumeProfile:
    resume = ResumeProfile(
        user=user,
        original_name="resume.pdf",
        extracted_text=(
            "教育经历 江苏科技大学\n专业技能 Python Django SQL\n"
            "InternFlow 项目：设计求职工作台并实现 20 项测试，效率提升 30%\n"
            "实习经历：负责开发和优化数据平台"
        ),
        analysis={
            "score": 78,
            "keywords": ["Python", "Django", "SQL"],
            "weaknesses": ["量化成果偏少。"],
        },
    )
    resume.file.save("resume.pdf", ContentFile(b"pdf"), save=True)
    return resume


@pytest.mark.django_db
def test_resume_center_requires_login(client):
    response = client.get(reverse("jobs:resume"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_uploads_and_analyzes_docx_and_refreshes_interview_prep(
    client,
    user,
    tmp_path,
    settings,
):
    settings.MEDIA_ROOT = tmp_path
    application = JobApplication.objects.create(
        user=user,
        company="云帆网络",
        role="Python 后端实习生",
        status=JobApplication.Status.INTERVIEW,
        job_description="熟悉 Python Django SQL",
    )
    text = (
        "教育经历\n江苏科技大学 软件工程\n专业技能\nPython Django SQL Git\n"
        "项目经历\nInternFlow 项目：负责设计并实现求职系统，完成 20 项测试，"
        "请求效率提升 35%\n实习经历\n开发数据平台并服务 100 个用户"
    )
    client.force_login(user)

    response = client.post(reverse("jobs:resume"), {"file": resume_docx(text)})

    resume = ResumeProfile.objects.get(user=user)
    assert response.status_code == 302
    assert resume.original_name == "我的简历.docx"
    assert resume.analysis["score"] >= 70
    assert application.prep_items.count() >= 5
    assert (tmp_path / resume.file.name).exists()


@pytest.mark.django_db
def test_resume_upload_shows_extraction_error(client, user, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(user)

    response = client.post(
        reverse("jobs:resume"),
        {"file": resume_docx("内容太短")},
    )

    assert response.status_code == 200
    assert "文字太少" in response.content.decode()
    assert not ResumeProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_resume_delete_removes_file_analysis_and_prep(
    client,
    user,
    application,
    tmp_path,
    settings,
):
    settings.MEDIA_ROOT = tmp_path
    resume = create_resume(user)
    item = InterviewPrepItem.objects.create(
        application=application,
        category=InterviewPrepItem.Category.RESUME,
        title="复习简历",
    )
    file_path = tmp_path / resume.file.name
    client.force_login(user)

    response = client.post(reverse("jobs:resume_delete"))

    assert response.status_code == 302
    assert not ResumeProfile.objects.filter(user=user).exists()
    assert not InterviewPrepItem.objects.filter(pk=item.pk).exists()
    assert not file_path.exists()


@pytest.mark.django_db
def test_interview_prep_redirects_to_resume_without_one(client, user, application):
    client.force_login(user)

    response = client.get(reverse("jobs:interview_prep", args=[application.pk]))

    assert response.status_code == 302
    assert response.url == reverse("jobs:resume")


@pytest.mark.django_db
def test_interview_prep_generates_toggles_and_refreshes(
    client,
    user,
    application,
    tmp_path,
    settings,
):
    settings.MEDIA_ROOT = tmp_path
    create_resume(user)
    application.status = JobApplication.Status.INTERVIEW
    application.job_description = "Python Django Redis"
    application.save()
    client.force_login(user)

    page_response = client.get(reverse("jobs:interview_prep", args=[application.pk]))
    item = application.prep_items.first()
    item_title = item.title
    toggle_response = client.post(
        reverse("jobs:interview_prep_toggle", args=[application.pk, item.pk]),
        {"is_done": "on"},
        headers={"HX-Request": "true"},
    )
    assert application.prep_items.get(title=item_title).is_done is True
    refresh_response = client.post(reverse("jobs:interview_prep_refresh", args=[application.pk]))

    assert page_response.status_code == 200
    assert toggle_response.status_code == 200
    assert 'id="prep-content"' in toggle_response.content.decode()
    assert refresh_response.status_code == 302
    assert application.prep_items.filter(title=item_title, is_done=True).exists()


@pytest.mark.django_db
def test_prep_toggle_hides_other_users_item(
    client,
    user,
    other_user,
    application,
):
    item = InterviewPrepItem.objects.create(
        application=application,
        category=InterviewPrepItem.Category.STORY,
        title="秘密清单",
    )
    client.force_login(other_user)

    response = client.post(
        reverse("jobs:interview_prep_toggle", args=[application.pk, item.pk]),
        {"is_done": "on"},
    )

    assert response.status_code == 404
