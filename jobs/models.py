from django.conf import settings
from django.db import models
from django.urls import reverse


class JobApplication(models.Model):
    """A job application owned by exactly one user."""

    class Status(models.TextChoices):
        SAVED = "saved", "待投递"
        APPLIED = "applied", "已投递"
        ASSESSMENT = "assessment", "笔试"
        INTERVIEW = "interview", "面试"
        OFFER = "offer", "Offer"
        CLOSED = "closed", "已结束"

    class Priority(models.TextChoices):
        LOW = "low", "低"
        MEDIUM = "medium", "中"
        HIGH = "high", "高"

    class WorkMode(models.TextChoices):
        ONSITE = "onsite", "现场"
        HYBRID = "hybrid", "混合"
        REMOTE = "remote", "远程"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
        verbose_name="用户",
    )
    company = models.CharField("公司", max_length=120)
    role = models.CharField("岗位", max_length=120)
    status = models.CharField(
        "进度",
        max_length=20,
        choices=Status.choices,
        default=Status.SAVED,
    )
    priority = models.CharField(
        "优先级",
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    work_mode = models.CharField(
        "工作方式",
        max_length=10,
        choices=WorkMode.choices,
        default=WorkMode.ONSITE,
    )
    location = models.CharField("地点", max_length=120, blank=True)
    source_url = models.URLField("职位链接", blank=True)
    salary_text = models.CharField("薪资", max_length=80, blank=True)
    deadline = models.DateField("截止日期", blank=True, null=True)
    applied_at = models.DateField("投递日期", blank=True, null=True)
    job_description = models.TextField("职位描述", blank=True)
    notes = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "投递记录"
        verbose_name_plural = "投递记录"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "deadline"]),
        ]

    def __str__(self) -> str:
        return f"{self.company} · {self.role}"

    def get_absolute_url(self) -> str:
        return reverse("jobs:detail", kwargs={"pk": self.pk})


class StatusChange(models.Model):
    """Immutable audit entry for a job application's progress."""

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="status_changes",
        verbose_name="投递记录",
    )
    from_status = models.CharField(
        "原进度",
        max_length=20,
        choices=JobApplication.Status.choices,
    )
    to_status = models.CharField(
        "新进度",
        max_length=20,
        choices=JobApplication.Status.choices,
    )
    created_at = models.DateTimeField("变更时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "进度变更"
        verbose_name_plural = "进度变更"

    def __str__(self) -> str:
        return f"{self.application}: {self.from_status} → {self.to_status}"
