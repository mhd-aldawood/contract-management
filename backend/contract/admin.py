from django.contrib import admin
from django.utils.html import format_html

from .educational_content.models import EducationalContent, PaymentScheduleItem
from .nafath_center.models import PaymentScheduleRow, NafathCenterAgreement
from .other.models import AgreementRow, Agreement
from .models import Profile, Role, RolePermission
from .doctoral_models import DoctoralContract

@admin.register(DoctoralContract)
class DoctoralContractAdmin(admin.ModelAdmin):
    list_display = ('agreement_number', 'name', 'doctor_rank', 'duration', 'is_hidden')
    search_fields = ('agreement_number', 'name', 'subject', 'commencement_order')


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    fields = ('feature', 'can_read', 'can_write', 'can_download')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    inlines = [RolePermissionInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'must_change_password', 'created_at')
    list_filter = ('role', 'must_change_password')
    search_fields = ('user__username', 'user__email')
    autocomplete_fields = ('user', 'role')


# ---------------- EducationalContent ----------------
class PaymentScheduleItemInline(admin.TabularInline):
    model = PaymentScheduleItem
    extra = 1
    fields = ("label", "amount", "due_date", "order")


@admin.register(EducationalContent)
class EducationalContentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "agreement_number", "company_name",
        "estimated_cost", "budget_type", "is_hidden", "created_at",
    )
    list_filter = ("type", "budget_type", "is_hidden", "payment_method")
    search_fields = ("name", "agreement_number", "company_name", "subject")
    readonly_fields = ("stored_name", "created_at", "updated_at")
    inlines = [PaymentScheduleItemInline]


@admin.register(PaymentScheduleItem)
class PaymentScheduleItemAdmin(admin.ModelAdmin):
    list_display = ("id", "content", "label", "amount", "due_date", "order")
    list_filter = ("due_date",)
    search_fields = ("label",)


# ---------------- NafathCenterAgreement ----------------
class PaymentScheduleRowInline(admin.TabularInline):
    model = PaymentScheduleRow
    extra = 1
    fields = ("label", "amount", "due_date", "order")
    ordering = ("order", "id")


@admin.register(NafathCenterAgreement)
class NafathCenterAgreementAdmin(admin.ModelAdmin):
    list_display = (
        "id", "agreement_number", "name", "company_name",
        "estimated_cost", "budget_type", "payment_method","payment_text",
        "start_date", "end_date", "is_hidden", "created_at",
    )
    list_filter = (
        "type", "budget_type", "payment_method", "is_hidden",
        "start_date", "end_date",
    )
    search_fields = ("name", "agreement_number", "company_name", "subject")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [PaymentScheduleRowInline]


@admin.register(PaymentScheduleRow)
class PaymentScheduleRowAdmin(admin.ModelAdmin):
    list_display = ("id", "agreement", "label", "amount", "due_date", "order")
    list_filter = ("due_date",)
    search_fields = ("label",)
    autocomplete_fields = ("agreement",)
    ordering = ("agreement", "order", "id")





#Other section

class AgreementRowInline(admin.TabularInline):
    model = AgreementRow
    extra = 1                       # show 1 empty row by default
    fields = ("order", "header", "body")
    ordering = ("order", "id")


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = (
        "agreement_number",
        "name",
        "type",
        "start_date",
        "end_date",
        "is_hidden",
        "rows_count",
        "file_link",
        "created_at",
    )
    list_filter = ("type", "is_hidden", "start_date", "end_date", "created_at")
    search_fields = ("agreement_number", "name", "file_name")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic info", {
            "fields": ("type", "agreement_number", "name")
        }),
        ("Dates", {
            "fields": ("start_date", "end_date")
        }),
        ("Visibility", {
            "fields": ("is_hidden",)
        }),
        ("File", {
            "fields": ("file_name", "file")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [AgreementRowInline]

    # ---- custom columns ------------------------------------------------
    @admin.display(description="Rows")
    def rows_count(self, obj):
        return obj.rows.count()

    @admin.display(description="File")
    def file_link(self, obj):
        if not obj.file:
            return "—"
        return format_html(
            '<a href="{}" target="_blank">Download</a>',
            obj.file.url,
        )


@admin.register(AgreementRow)
class AgreementRowAdmin(admin.ModelAdmin):
    list_display = ("id", "agreement", "order", "header")
    list_filter = ("agreement",)
    search_fields = ("header", "body", "agreement__agreement_number")
    autocomplete_fields = ("agreement",)      # requires search_fields on AgreementAdmin
    ordering = ("agreement", "order", "id")
