
from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "full_name",
        "work_email",
        "department",
        "job_title",
        "joining_date",
    )

    search_fields = ("employee_id", "full_name", "work_email")
    list_filter = ("department", "job_title")
