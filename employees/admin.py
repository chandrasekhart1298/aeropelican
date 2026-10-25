from django.contrib import admin
from .models import Attendance, AuditLog, Employee, LeaveBalance, LeaveRequest, Payslip

class SuperuserOnlyAdminSite(admin.AdminSite):
    site_header = "AeroPeople Administration"
    site_title = "AeroPeople Admin"
    index_title = "Restricted administration"
    def has_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

# Replace the default site class so ordinary staff users cannot enter /admin/.
admin.site.__class__ = SuperuserOnlyAdminSite

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display=("employee_id","full_name","work_email","department","job_title","joining_date","user","is_active")
    search_fields=("employee_id","full_name","work_email","department","job_title")
    list_filter=("department","job_title","is_active")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display=("employee","work_date","clock_in","clock_out","status")
    list_filter=("status","work_date")
    search_fields=("employee__employee_id","employee__full_name")

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display=("employee","leave_type","year","entitled_days","used_days")
    list_filter=("leave_type","year")

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display=("employee","leave_type","start_date","end_date","status","reviewer")
    list_filter=("status","leave_type")
    readonly_fields=("created_at","reviewed_at")

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display=("employee","period_start","period_end","gross_pay","deductions","net_pay","published")
    list_filter=("published","period_end")
    readonly_fields=("created_at","published_at")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display=("created_at","actor","action","object_type","object_id")
    readonly_fields=("actor","action","object_type","object_id","details","ip_address","created_at")
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
