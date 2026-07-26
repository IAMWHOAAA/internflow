from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import JobApplication, StatusChange


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
            application, was_created = JobApplication.objects.get_or_create(
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

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        if created:
            self.stdout.write(f"Username: {username}")
            self.stdout.write(f"Password: {password}")
        else:
            self.stdout.write("The demo user already existed; its password was not changed.")
