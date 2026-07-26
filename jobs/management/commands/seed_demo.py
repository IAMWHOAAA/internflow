from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from docx import Document

from jobs.models import JobApplication, ResumeProfile, StatusChange
from jobs.services.interview_prep import refresh_interview_prep
from jobs.services.resume_analysis import analyze_resume

DEMO_RESUME_TEXT = """李明 | Python 后端开发实习生
教育经历
江苏科技大学 计算机相关专业 本科 2023-2027
专业技能
熟悉 Python、Django、SQL、Git、Docker、Linux 与 HTTP，能够使用 pytest 编写单元测试。
项目经历
InternFlow 实习投递管理项目
负责使用 Django 设计用户权限、投递看板和状态流转，实现简历解析与面试清单功能。
使用 Docker 完成本地部署，通过 GitHub Actions 自动运行 41 项测试，测试覆盖率达到 93%。
校园预约系统项目
设计预约冲突校验和数据库模型，优化查询后接口响应时间降低 35%。
实践经历
参与校内软件项目协作，负责需求拆分、代码评审与缺陷修复，累计完成 12 项任务。
个人总结
持续学习后端工程实践，能够清晰说明技术取舍、问题定位过程和项目改进方向。
"""


class Command(BaseCommand):
    help = "Create a local demo account with realistic application data."

    def handle(self, *args, **options):
        username = "demo"
        password = "internflow-demo-2026"
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])

        today = timezone.localdate()
        examples = [
            {
                "company": "星河科技",
                "role": "Python 开发实习生",
                "status": JobApplication.Status.APPLIED,
                "priority": JobApplication.Priority.HIGH,
                "location": "南京",
                "work_mode": JobApplication.WorkMode.ONSITE,
                "salary_text": "200–250 元/天",
                "applied_at": today - timedelta(days=2),
                "notes": "岗位技术栈与 Django 项目经验匹配，准备项目亮点。",
            },
            {
                "company": "云帆网络",
                "role": "后端开发实习生",
                "status": JobApplication.Status.INTERVIEW,
                "priority": JobApplication.Priority.HIGH,
                "location": "杭州",
                "work_mode": JobApplication.WorkMode.HYBRID,
                "salary_text": "250 元/天",
                "applied_at": today - timedelta(days=8),
                "notes": "技术一面：复习数据库索引、HTTP 和项目权限设计。",
                "interview_at": timezone.now() + timedelta(days=1),
                "job_description": (
                    "熟悉 Python、Django、SQL 和 HTTP，了解 Docker、Linux，"
                    "能够编写自动化测试并独立完成后端功能。"
                ),
            },
            {
                "company": "远山数据",
                "role": "数据分析实习生",
                "status": JobApplication.Status.ASSESSMENT,
                "priority": JobApplication.Priority.MEDIUM,
                "location": "上海",
                "work_mode": JobApplication.WorkMode.HYBRID,
                "applied_at": today - timedelta(days=4),
            },
            {
                "company": "青桐智能",
                "role": "AI 应用开发实习生",
                "status": JobApplication.Status.SAVED,
                "priority": JobApplication.Priority.HIGH,
                "location": "苏州",
                "work_mode": JobApplication.WorkMode.ONSITE,
                "deadline": today + timedelta(days=3),
                "salary_text": "220–300 元/天",
            },
            {
                "company": "海岸互联",
                "role": "软件工程实习生",
                "status": JobApplication.Status.OFFER,
                "priority": JobApplication.Priority.MEDIUM,
                "location": "远程",
                "work_mode": JobApplication.WorkMode.REMOTE,
                "applied_at": today - timedelta(days=21),
            },
            {
                "company": "方舟软件",
                "role": "测试开发实习生",
                "status": JobApplication.Status.CLOSED,
                "priority": JobApplication.Priority.LOW,
                "location": "南京",
                "work_mode": JobApplication.WorkMode.ONSITE,
                "applied_at": today - timedelta(days=30),
            },
        ]

        for data in examples:
            application, was_created = JobApplication.objects.update_or_create(
                user=user,
                company=data["company"],
                role=data["role"],
                defaults=data,
            )
            if was_created:
                StatusChange.objects.create(
                    application=application,
                    from_status=application.status,
                    to_status=application.status,
                )

        resume, resume_created = ResumeProfile.objects.get_or_create(
            user=user,
            defaults={
                "original_name": "demo-resume.docx",
                "content_type": (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ),
                "extracted_text": DEMO_RESUME_TEXT,
                "analysis": analyze_resume(DEMO_RESUME_TEXT),
                "analyzed_at": timezone.now(),
            },
        )
        if resume_created:
            document = Document()
            for line in DEMO_RESUME_TEXT.splitlines():
                document.add_paragraph(line)
            buffer = BytesIO()
            document.save(buffer)
            resume.file.save(
                "demo-resume.docx",
                ContentFile(buffer.getvalue()),
                save=True,
            )

        interview = JobApplication.objects.get(
            user=user,
            company="云帆网络",
            role="后端开发实习生",
        )
        refresh_interview_prep(interview, resume)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        if created:
            self.stdout.write(f"Username: {username}")
            self.stdout.write(f"Password: {password}")
        else:
            self.stdout.write("The demo user already existed; its password was not changed.")
