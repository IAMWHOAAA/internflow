from django.contrib import admin

from .models import InterviewPrepItem, JobApplication, ResumeProfile, StatusChange


class StatusChangeInline(admin.TabularInline):
    model = StatusChange
    extra = 0
    readonly_fields = ("from_status", "to_status", "created_at")
    can_delete = False


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("company", "role", "user", "status", "priority", "deadline", "updated_at")
    list_filter = ("status", "priority", "work_mode")
    search_fields = ("company", "role", "user__username")
    inlines = [StatusChangeInline]


@admin.register(StatusChange)
class StatusChangeAdmin(admin.ModelAdmin):
    list_display = ("application", "from_status", "to_status", "created_at")
    list_filter = ("to_status",)
    readonly_fields = ("application", "from_status", "to_status", "created_at")


@admin.register(ResumeProfile)
class ResumeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "original_name", "analyzed_at", "updated_at")
    search_fields = ("user__username", "original_name")
    readonly_fields = ("extracted_text", "analysis", "analyzed_at", "created_at", "updated_at")


@admin.register(InterviewPrepItem)
class InterviewPrepItemAdmin(admin.ModelAdmin):
    list_display = ("title", "application", "category", "is_done", "position")
    list_filter = ("category", "is_done")
    search_fields = ("title", "application__company", "application__role")
