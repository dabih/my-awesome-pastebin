import json

from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Category, Paste, Report, VisitCount
from .tasks import generate_daily_frequency_report, generate_top_pastes_report


class VisitCountInline(admin.TabularInline):
    model = VisitCount
    extra = 0
    readonly_fields = ("count", "last_updated")
    can_delete = False
    max_num = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)


@admin.register(Paste)
class PasteAdmin(admin.ModelAdmin):
    list_display = ("title", "uid", "category", "syntax", "burn_after_read", "expiration_datetime", "deleted", "created_at")
    list_filter = ("category", "deleted", "burn_after_read", "syntax")
    search_fields = ("title", "uid")
    readonly_fields = ("uid", "created_at")
    date_hierarchy = "created_at"
    inlines = [VisitCountInline]


@admin.register(VisitCount)
class VisitCountAdmin(admin.ModelAdmin):
    list_display = ("paste", "count", "last_updated")
    readonly_fields = ("paste", "last_updated")
    search_fields = ("paste__title", "paste__uid")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("type", "created_at")
    list_filter = ("type",)
    readonly_fields = ("type", "created_at", "formatted_data")
    exclude = ("data",)
    actions = ["action_generate_top_pastes", "action_generate_daily_frequency"]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Data")
    def formatted_data(self, obj):
        return format_html("<pre style='white-space:pre-wrap'>{}</pre>", json.dumps(obj.data, indent=2, ensure_ascii=False))

    @admin.action(description="Generate Top-10 Popular Pastes report now")
    def action_generate_top_pastes(self, request, queryset):
        generate_top_pastes_report.delay()
        self.message_user(request, "Top pastes report task queued.", messages.SUCCESS)

    @admin.action(description="Generate Daily Frequency report now")
    def action_generate_daily_frequency(self, request, queryset):
        generate_daily_frequency_report.delay()
        self.message_user(request, "Daily frequency report task queued.", messages.SUCCESS)
