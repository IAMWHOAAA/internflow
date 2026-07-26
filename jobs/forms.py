import re
from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import JobApplication, ResumeProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="邮箱", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password and (not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password)):
            raise ValidationError("密码必须同时包含字母和数字。")
        return password


class JobApplicationForm(forms.ModelForm):
    source_url = forms.URLField(
        label="职位链接",
        required=False,
        assume_scheme="https",
    )

    class Meta:
        model = JobApplication
        fields = (
            "company",
            "role",
            "status",
            "priority",
            "work_mode",
            "location",
            "source_url",
            "salary_text",
            "deadline",
            "applied_at",
            "interview_at",
            "job_description",
            "notes",
        )
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "applied_at": forms.DateInput(attrs={"type": "date"}),
            "interview_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "job_description": forms.Textarea(attrs={"rows": 5}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }


class ResumeUploadForm(forms.ModelForm):
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".pdf", ".docx"}
    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    }

    class Meta:
        model = ResumeProfile
        fields = ("file",)
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "accept": (
                        ".pdf,.docx,application/pdf,"
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                }
            )
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        extension = Path(uploaded_file.name).suffix.lower()
        content_type = getattr(uploaded_file, "content_type", "")

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValidationError("只支持 PDF 或 DOCX 格式。")
        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise ValidationError("简历文件不能超过 5 MB。")
        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError("文件类型与扩展名不匹配。")
        return uploaded_file
