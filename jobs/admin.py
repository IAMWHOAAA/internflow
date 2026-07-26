from django.contrib import admin

from .models import JobApplication, StatusChange


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
