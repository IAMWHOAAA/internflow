import pytest
from django.core.files.base import ContentFile

from jobs.models import InterviewPrepItem, ResumeProfile
from jobs.services.interview_prep import build_prep_items, refresh_interview_prep


@pytest.fixture
def resume(user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    resume = ResumeProfile(
        user=user,
        original_name="resume.pdf",
        extracted_text=(
            "教育经历\n专业技能 Python Django SQL\n"
            "InternFlow 项目：使用 Django 构建投递管理工具并完成自动化测试"
        ),
        analysis={
            "keywords": ["Python", "Django", "SQL"],
            "weaknesses": ["量化成果偏少。"],
        },
    )
    resume.file.save("resume.pdf", ContentFile(b"pdf"), save=True)
    return resume


@pytest.mark.django_db
def test_builds_personalized_items_from_resume_and_job(application, resume):
    application.role = "Python 后端开发实习生"
    application.job_description = "熟悉 Python、Django、Redis 和 Docker"

    items = build_prep_items(application, resume)
    titles = [item["title"] for item in items]

    assert any("共同技术" in title and "Python" in title for title in titles)
    assert any("JD 关键词" in title and "Redis" in title for title in titles)
    assert any("InternFlow 项目" in title for title in titles)
    assert any("量化成果" in title for title in titles)


@pytest.mark.django_db
def test_builds_fallback_items_without_jd_or_project(application, resume):
    resume.extracted_text = "教育经历\n专业技能 Python"
    application.role = "运营实习生"
    application.job_description = ""

    items = build_prep_items(application, resume)
    titles = [item["title"] for item in items]

    assert any("补充岗位 JD" in title for title in titles)
    assert any("选择 2 个" in title for title in titles)


@pytest.mark.django_db
def test_refresh_preserves_completed_items(application, resume):
    first_items = refresh_interview_prep(application, resume)
    first_items[0].is_done = True
    first_items[0].save(update_fields=["is_done"])
    completed_title = first_items[0].title

    refreshed = refresh_interview_prep(application, resume)

    assert len(refreshed) >= 5
    assert application.prep_items.get(title=completed_title).is_done is True
    assert application.prep_items.count() == len(refreshed)


@pytest.mark.django_db
def test_prep_item_string(application):
    item = InterviewPrepItem.objects.create(
        application=application,
        category=InterviewPrepItem.Category.STORY,
        title="准备自我介绍",
    )

    assert str(item) == "准备自我介绍"
