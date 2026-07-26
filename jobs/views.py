from collections import OrderedDict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import JobApplicationForm, SignUpForm
from .models import JobApplication, StatusChange


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
    return {
        "grouped_applications": grouped,
        "query": query,
        "selected_status": status,
        "status_choices": JobApplication.Status.choices,
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
        messages.success(
            request,
            f"已将 {application.company} 更新为{application.get_status_display()}。",
        )

    return redirect("jobs:dashboard")
