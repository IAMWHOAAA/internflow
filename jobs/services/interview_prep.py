import re

from django.db import transaction

from jobs.models import InterviewPrepItem, JobApplication, ResumeProfile
from jobs.services.resume_analysis import extract_keywords


def _project_lines(text: str) -> list[str]:
    candidates = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip(" -•|")
        if 8 <= len(line) <= 90 and ("项目" in line or "project" in line.lower()):
            if line.lower() not in {"项目经历", "项目经验", "projects", "project experience"}:
                candidates.append(line)
    return candidates[:2]


def build_prep_items(
    application: JobApplication,
    resume: ResumeProfile,
) -> list[dict]:
    """Combine resume signals and job requirements into a concise checklist."""
    analysis = resume.analysis or {}
    resume_keywords = set(analysis.get("keywords", []))
    role_text = f"{application.role}\n{application.job_description}"
    role_keywords = set(extract_keywords(role_text))
    overlap = sorted(resume_keywords & role_keywords)
    gaps = sorted(role_keywords - resume_keywords)

    items = [
        {
            "category": InterviewPrepItem.Category.STORY,
            "title": "准备 90 秒自我介绍",
            "detail": f"围绕“为什么适合 {application.company} 的 {application.role}”组织经历。",
        },
        {
            "category": InterviewPrepItem.Category.POSITION,
            "title": f"研究 {application.company} 与岗位要求",
            "detail": "整理业务方向、岗位职责、你的匹配点，以及准备向面试官提出的 3 个问题。",
        },
        {
            "category": InterviewPrepItem.Category.STORY,
            "title": "准备 3 个 STAR 行为故事",
            "detail": "覆盖解决难题、团队协作和一次失败复盘，每个故事控制在 2 分钟。",
        },
    ]

    if overlap:
        items.append(
            {
                "category": InterviewPrepItem.Category.FUNDAMENTAL,
                "title": f"复习岗位与简历共同技术：{'、'.join(overlap[:5])}",
                "detail": "每项准备原理、实际使用场景、踩过的坑和一次取舍。",
            }
        )
    if gaps:
        items.append(
            {
                "category": InterviewPrepItem.Category.POSITION,
                "title": f"补齐 JD 关键词：{'、'.join(gaps[:5])}",
                "detail": "先理解核心概念，再准备诚实说明学习进度，避免把未使用过的技术写成熟练。",
            }
        )
    if not role_keywords:
        items.append(
            {
                "category": InterviewPrepItem.Category.POSITION,
                "title": "补充岗位 JD 并提炼 5 个核心要求",
                "detail": "当前职位描述不足，补充后重新生成可获得更具体的技术清单。",
            }
        )

    project_lines = _project_lines(resume.extracted_text)
    if project_lines:
        for project in project_lines:
            items.append(
                {
                    "category": InterviewPrepItem.Category.PROJECT,
                    "title": f"深挖项目：{project[:60]}",
                    "detail": "准备架构图、个人贡献、最难问题、技术取舍、结果数据和可改进之处。",
                }
            )
    else:
        items.append(
            {
                "category": InterviewPrepItem.Category.PROJECT,
                "title": "选择 2 个最能代表你的项目深入复盘",
                "detail": "重点说明你亲自完成的部分，准备回答“为什么这样设计”。",
            }
        )

    for weakness in analysis.get("weaknesses", [])[:2]:
        items.append(
            {
                "category": InterviewPrepItem.Category.RESUME,
                "title": f"补强简历短板：{weakness}",
                "detail": "准备口头补充材料；如果事实允许，面试前同步优化简历表述。",
            }
        )

    items.append(
        {
            "category": InterviewPrepItem.Category.RESUME,
            "title": "逐行检查简历，确保每一句都能经得住追问",
            "detail": "尤其确认技术熟练度、数字、项目角色和时间线准确一致。",
        }
    )
    return items[:12]


@transaction.atomic
def refresh_interview_prep(
    application: JobApplication,
    resume: ResumeProfile,
) -> list[InterviewPrepItem]:
    """Regenerate a checklist while preserving completed items by title."""
    completed_titles = set(
        application.prep_items.filter(is_done=True).values_list("title", flat=True)
    )
    application.prep_items.all().delete()
    created = InterviewPrepItem.objects.bulk_create(
        [
            InterviewPrepItem(
                application=application,
                category=item["category"],
                title=item["title"],
                detail=item["detail"],
                is_done=item["title"] in completed_titles,
                position=position,
            )
            for position, item in enumerate(build_prep_items(application, resume), start=1)
        ]
    )
    return created
