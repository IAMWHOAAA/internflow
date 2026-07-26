from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import JobApplication


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="邮箱", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


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
            "job_description",
            "notes",
        )
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "applied_at": forms.DateInput(attrs={"type": "date"}),
            "job_description": forms.Textarea(attrs={"rows": 5}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
