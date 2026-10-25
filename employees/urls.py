from django.urls import path
from . import views
from . import audit_views

urlpatterns = [
    path("", views.home, name="home"),
    path("employees/", views.employee_directory, name="employee_directory"),
    path("employees/create/", views.employee_create, name="employee_create"),
    path("employees/<int:employee_id>/", views.employee_profile, name="employee_profile"),
    path("employees/<int:employee_id>/manage/", views.employee_manage, name="employee_manage"),
    path("audit-history/", audit_views.audit_history, name="audit_history"),
    path("attendance/", views.attendance, name="attendance"),
    path("attendance/clock-in/", views.clock_in, name="clock_in"),
    path("attendance/clock-out/", views.clock_out, name="clock_out"),
    path("leave/", views.leave_list, name="leave_list"),
    path("leave/apply/", views.leave_apply, name="leave_apply"),
    path("leave/<int:leave_id>/<str:decision>/", views.leave_review, name="leave_review"),
    path("payroll/payslips/", views.payslip_list, name="payslip_list"),
    path("payroll/payslips/<int:payslip_id>/", views.payslip_detail, name="payslip_detail"),
    path("payroll/payslips/<int:payslip_id>/publish/", views.payslip_publish, name="payslip_publish"),
]
