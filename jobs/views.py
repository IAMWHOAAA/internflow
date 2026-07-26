from collections import OrderedDict
from datetime import timedelta
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import JobApplicationForm, ResumeUploadForm, SignUpForm
from .models import InterviewPrepItem, JobApplication, ResumeProfile, StatusChange
from .services.interview_prep import refresh_interview_prep
from .services.resume_analysis import ResumeExtractionError, analyze_resume, extract_resume_text


def landing(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("jobs:dashboard")
    return render(request, "landing.html")


def signup(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("jobs:dashboard")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "账户创建成功，开始记录你的第一份投递吧。")
        return redirect("jobs:dashboard")
    return render(request, "registration/signup.html", {"form": form})


def _dashboard_context(request: HttpRequest) -> dict:
    applications = JobApplication.objects.filter(user=request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        applications = applications.filter(
            Q(company__icontains=query)
            | Q(role__icontains=query)
            | Q(location__icontains=query)
            | Q(notes__icontains=query)
        )
    if status in JobApplication.Status.values:
        applications = applications.filter(status=status)

    grouped = OrderedDict(
        (value, {"label": label, "items": []}) for value, label in JobApplication.Status.choices
    )
    for application in applications:
        grouped[application.status]["items"].append(application)

    all_applications = JobApplication.objects.filter(user=request.user)
    today = timezone.localdate()
    resume = ResumeProfile.objects.filter(user=request.user).first()
    return {
        "grouped_applications": grouped,
        "query": query,
        "selected_status": status,
        "status_choices": JobApplication.Status.choices,
        "resume": resume,
        "upcoming_interviews": all_applications.filter(
            status=JobApplication.Status.INTERVIEW
        ).order_by(F("interview_at").asc(nulls_last=True))[:3],
        "stats": {
            "total": all_applications.count(),
            "active": all_applications.exclude(
                status__in=[JobApplication.Status.OFFER, JobApplication.Status.CLOSED]
            ).count(),
            "interviews": all_applications.filter(status=JobApplication.Status.INTERVIEW).count(),
            "offers": all_applications.filter(status=JobApplication.Status.OFFER).count(),
            "due_soon": all_applications.filter(
                status=JobApplication.Status.SAVED,
                deadline__range=(today, today + timedelta(days=7)),
            ).count(),
        },
    }


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    template = (
        "jobs/partials/dashboard_content.html"
        if request.headers.get("HX-Request") == "true"
        else "jobs/dashboard.html"
    )
    return render(request, template, _dashboard_context(request))


def _refresh_prep_if_ready(application: JobApplication) -> None:
    if application.status != JobApplication.Status.INTERVIEW:
        return
    resume = ResumeProfile.objects.filter(user=application.user).first()
    if resume and resume.analysis:
        refresh_interview_prep(application, resume)


@login_required
def application_create(request: HttpRequest) -> HttpResponse:
    form = JobApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.save()
        StatusChange.objects.create(
            application=application,
            from_status=application.status,
            to_status=application.status,
        )
        _refresh_prep_if_ready(application)
        messages.success(request, "投递记录已创建。")
        return redirect(application)
    return render(
        request,
        "jobs/application_form.html",
        {"form": form, "page_title": "新增投递"},
    )


def _owned_application(request: HttpRequest, pk: int) -> JobApplication:
    return get_object_or_404(JobApplication, pk=pk, user=request.user)


@login_required
def application_detail(request: HttpRequest, pk: int) -> HttpResponse:
    application = _owned_application(request, pk)
    return render(request, "jobs/application_detail.html", {"application": application})


@login_required
def application_edit(request: HttpRequest, pk: int) -> HttpResponse:
    application = _owned_application(request, pk)
    previous_status = application.status
    form = JobApplicationForm(request.POST or None, instance=application)
    if request.method == "POST" and form.is_valid():
        updated = form.save()
        if updated.status != previous_status:
            StatusChange.objects.create(
                application=updated,
                from_status=previous_status,
                to_status=updated.status,
            )
        if updated.status == JobApplication.Status.INTERVIEW:
            _refresh_prep_if_ready(updated)
        messages.success(request, "投递记录已更新。")
        return redirect(updated)
    return render(
        request,
        "jobs/application_form.html",
        {"form": form, "application": application, "page_title": "编辑投递"},
    )


@login_required
def application_delete(request: HttpRequest, pk: int) -> HttpResponse:
    application = _owned_application(request, pk)
    if request.method == "POST":
        application.delete()
        messages.success(request, "投递记录已删除。")
        return redirect("jobs:dashboard")
    return render(request, "jobs/application_confirm_delete.html", {"application": application})


@login_required
@transaction.atomic
def application_status_update(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("只接受 POST 请求")

    application = get_object_or_404(
        JobApplication.objects.select_for_update(),
        pk=pk,
        user=request.user,
    )
    new_status = request.POST.get("status", "")
    if new_status not in JobApplication.Status.values:
        return HttpResponseBadRequest("无效的投递进度")

    if application.status != new_status:
        previous_status = application.status
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])
        StatusChange.objects.create(
            application=application,
            from_status=previous_status,
            to_status=new_status,
        )
        _refresh_prep_if_ready(application)
        messages.success(
            request,
            f"已将 {application.company} 更新为{application.get_status_display()}。",
        )

    return redirect("jobs:dashboard")


@login_required
def resume_center(request: HttpRequest) -> HttpResponse:
    resume = ResumeProfile.objects.filter(user=request.user).first()
    form = ResumeUploadForm(
        request.POST or None,
        request.FILES or None,
        instance=resume,
    )

    if request.method == "POST" and form.is_valid():
        uploaded_file = form.cleaned_data["file"]
        try:
            extracted_text = extract_resume_text(uploaded_file)
        except ResumeExtractionError as error:
            form.add_error("file", str(error))
        else:
            old_file_name = resume.file.name if resume and resume.file else None
            profile = form.save(commit=False)
            profile.user = request.user
            profile.original_name = Path(uploaded_file.name).name
            profile.content_type = getattr(uploaded_file, "content_type", "")
            profile.extracted_text = extracted_text
            profile.analysis = analyze_resume(extracted_text)
            profile.analyzed_at = timezone.now()
            profile.save()

            if old_file_name and old_file_name != profile.file.name:
                profile.file.storage.delete(old_file_name)

            interview_applications = JobApplication.objects.filter(
                user=request.user,
                status=JobApplication.Status.INTERVIEW,
            )
            for application in interview_applications:
                refresh_interview_prep(application, profile)

            messages.success(request, "简历分析完成，面试清单已同步更新。")
            return redirect("jobs:resume")

    return render(
        request,
        "jobs/resume_center.html",
        {"form": form, "resume": resume},
    )


@login_required
def resume_delete(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("只接受 POST 请求")
    resume = get_object_or_404(ResumeProfile, user=request.user)
    file_storage = resume.file.storage
    file_name = resume.file.name
    InterviewPrepItem.objects.filter(application__user=request.user).delete()
    resume.delete()
    if file_name:
        file_storage.delete(file_name)
    messages.success(request, "简历及分析结果已删除。")
    return redirect("jobs:resume")


def _prep_context(application: JobApplication) -> dict:
    items = application.prep_items.all()
    grouped = OrderedDict(
        (value, {"label": label, "items": []})
        for value, label in InterviewPrepItem.Category.choices
    )
    for item in items:
        grouped[item.category]["items"].append(item)
    total = items.count()
    completed = items.filter(is_done=True).count()
    return {
        "application": application,
        "grouped_prep": grouped,
        "prep_total": total,
        "prep_completed": completed,
        "prep_progress": round(completed / total * 100) if total else 0,
    }


@login_required
def interview_prep(request: HttpRequest, pk: int) -> HttpResponse:
    application = _owned_application(request, pk)
    resume = ResumeProfile.objects.filter(user=request.user).first()
    if not resume:
        messages.warning(request, "请先上传简历，再生成个性化面试清单。")
        return redirect("jobs:resume")
    if not application.prep_items.exists():
        refresh_interview_prep(application, resume)
    return render(request, "jobs/interview_prep.html", _prep_context(application))


@login_required
def interview_prep_refresh(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("只接受 POST 请求")
    application = _owned_application(request, pk)
    resume = get_object_or_404(ResumeProfile, user=request.user)
    refresh_interview_prep(application, resume)
    messages.success(request, "已根据最新简历和职位描述重新生成清单。")
    return redirect("jobs:interview_prep", pk=application.pk)


@login_required
def interview_prep_toggle(request: HttpRequest, pk: int, item_pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("只接受 POST 请求")
    application = _owned_application(request, pk)
    item = get_object_or_404(
        InterviewPrepItem,
        pk=item_pk,
        application=application,
    )
    item.is_done = request.POST.get("is_done") == "on"
    item.save(update_fields=["is_done"])
    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "jobs/partials/prep_content.html",
            _prep_context(application),
        )
    return redirect("jobs:interview_prep", pk=application.pk)
