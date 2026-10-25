from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EmployeeAccountForm, LeaveRequestForm
from .models import Attendance, AuditLog, Employee, LeaveBalance, LeaveRequest, Payslip
from .permissions import ROLE_HR, ROLE_MANAGER, ROLE_PAYROLL, employee_or_role_allowed, has_role, linked_employee


def audit(request, action, obj):
    AuditLog.objects.create(
        actor=request.user, action=action,
        object_type=obj.__class__.__name__, object_id=str(obj.pk),
        ip_address=request.META.get("REMOTE_ADDR"),
    )


def is_hr_or_admin(user):
    return user.is_superuser or has_role(user, ROLE_HR)


def is_payroll_or_admin(user):
    return user.is_superuser or has_role(user, ROLE_PAYROLL)


def can_review_leave(user):
    return user.is_superuser or has_role(user, ROLE_HR, ROLE_MANAGER)


def visible_leave_requests(user):
    qs = LeaveRequest.objects.select_related("employee", "reviewer")
    if is_hr_or_admin(user):
        return qs
    if has_role(user, ROLE_MANAGER):
        manager = linked_employee(user)
        return qs.filter(employee__manager=manager) if manager else qs.none()
    return qs.none()


@login_required
def home(request):
    employee = linked_employee(request.user)
    elevated = request.user.is_superuser or has_role(
        request.user, ROLE_HR, ROLE_MANAGER, ROLE_PAYROLL
    )
    ctx = {
        "employee": employee,
        "total_employees": None,
        "pending_leave_count": None,
        "can_view_directory": is_hr_or_admin(request.user),
        "can_review_leave": can_review_leave(request.user),
        "can_manage_payroll": is_payroll_or_admin(request.user),
    }
    if elevated:
        ctx["total_employees"] = Employee.objects.filter(is_active=True).count()
        ctx["pending_leave_count"] = LeaveRequest.objects.filter(status="pending").count()
    return render(request, "employees/home.html", ctx)


@login_required
def employee_directory(request):
    if not is_hr_or_admin(request.user):
        raise PermissionDenied("Only HR and administrators can access the employee directory.")
    query = request.GET.get("q", "").strip()
    employees = Employee.objects.filter(is_active=True).select_related("user").order_by("employee_id")
    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query) | Q(full_name__icontains=query)
            | Q(work_email__icontains=query) | Q(department__icontains=query)
            | Q(job_title__icontains=query)
        )
    return render(request, "employees/directory.html", {"employees": employees, "query": query})


@login_required
def employee_create(request):
    if not is_hr_or_admin(request.user):
        raise PermissionDenied("Only HR and administrators can create employee accounts.")
    form = EmployeeAccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save_user()
            employee = form.save_employee(user)
            employee_group, _ = Group.objects.get_or_create(name="Employee")
            user.groups.add(employee_group)
            audit(request, "employee.account_created", employee)
        messages.success(request, f"Account created for {employee.full_name}. Share the initial password securely.")
        return redirect("employee_profile", employee_id=employee.pk)
    return render(request, "employees/employee_form.html", {"form": form})


@login_required
def employee_profile(request, employee_id):
    employee = get_object_or_404(
        Employee.objects.select_related("user", "manager"),
        pk=employee_id, is_active=True,
    )
    if not employee_or_role_allowed(request.user, employee, ROLE_HR):
        raise PermissionDenied("You are not authorized to view this employee profile.")
    return render(request, "employees/profile.html", {"employee": employee})


@login_required
def attendance(request):
    employee = linked_employee(request.user)
    is_admin_hr = is_hr_or_admin(request.user)
    if is_admin_hr:
        history = Attendance.objects.select_related("employee").order_by("-work_date", "-clock_in")
        selected_employee = request.GET.get("employee", "").strip()
        selected_date = request.GET.get("date", "").strip()
        if selected_employee.isdigit():
            history = history.filter(employee_id=int(selected_employee))
        if selected_date:
            history = history.filter(work_date=selected_date)
        record = Attendance.objects.filter(
            employee=employee, work_date=timezone.localdate()
        ).first() if employee else None
        employees = Employee.objects.filter(is_active=True).order_by("full_name")
    elif employee and employee.is_active:
        record = Attendance.objects.filter(employee=employee, work_date=timezone.localdate()).first()
        history = Attendance.objects.filter(employee=employee).order_by("-work_date")[:60]
        employees = []
        selected_employee = selected_date = ""
    else:
        raise PermissionDenied("Your login is not linked to an active employee profile. Contact HR.")
    return render(request, "employees/attendance.html", {
        "record": record, "history": history[:200] if is_admin_hr else history,
        "is_admin_hr": is_admin_hr, "employee": employee, "employees": employees,
        "selected_employee": selected_employee, "selected_date": selected_date,
    })


@login_required
@require_POST
def clock_in(request):
    employee = linked_employee(request.user)
    if not employee or not employee.is_active:
        raise PermissionDenied("Clock-in requires an active employee profile linked to your account.")
    today = timezone.localdate()
    with transaction.atomic():
        record, created = Attendance.objects.get_or_create(
            employee=employee, work_date=today,
            defaults={"clock_in": timezone.now(), "status": Attendance.Status.PRESENT},
        )
        if not created:
            if record.clock_in:
                messages.error(request, "You have already marked Present today.")
                return redirect("attendance")
            record.clock_in = timezone.now()
            record.status = Attendance.Status.PRESENT
            record.save(update_fields=["clock_in", "status"])
        audit(request, "attendance.clock_in", record)
    messages.success(request, "Present recorded with the server time.")
    return redirect("attendance")


@login_required
@require_POST
def clock_out(request):
    employee = linked_employee(request.user)
    if not employee or not employee.is_active:
        raise PermissionDenied("Clock-out requires an active employee profile linked to your account.")
    with transaction.atomic():
        record = get_object_or_404(
            Attendance.objects.select_for_update(),
            employee=employee, work_date=timezone.localdate(),
        )
        if not record.clock_in or record.clock_out:
            messages.error(request, "Clock in first; clock-out can be recorded only once.")
            return redirect("attendance")
        record.clock_out = timezone.now()
        record.save(update_fields=["clock_out"])
        audit(request, "attendance.clock_out", record)
    messages.success(request, "Clock-out time recorded.")
    return redirect("attendance")


@login_required
def leave_list(request):
    employee = linked_employee(request.user)
    reviewer = can_review_leave(request.user)
    if is_hr_or_admin(request.user):
        requests = LeaveRequest.objects.select_related("employee", "reviewer")
    elif has_role(request.user, ROLE_MANAGER):
        requests = visible_leave_requests(request.user)
    elif employee:
        requests = LeaveRequest.objects.filter(employee=employee).select_related("employee", "reviewer")
    else:
        raise PermissionDenied("Your login is not linked to an employee profile.")
    balances = LeaveBalance.objects.filter(
        employee=employee, year=timezone.localdate().year
    ) if employee else LeaveBalance.objects.none()
    return render(request, "employees/leave_list.html", {
        "leave_requests": requests, "balances": balances, "can_review": reviewer,
    })


@login_required
def leave_apply(request):
    employee = linked_employee(request.user)
    if not employee or not employee.is_active:
        raise PermissionDenied("An active linked employee account is required to apply for leave.")
    form = LeaveRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        leave = form.save(commit=False)
        leave.employee = employee
        leave.save()
        audit(request, "leave.created", leave)
        messages.success(request, "Leave request submitted.")
        return redirect("leave_list")
    return render(request, "employees/leave_form.html", {"form": form})


@login_required
@require_POST
def leave_review(request, leave_id, decision):
    if not can_review_leave(request.user) or decision not in ("approve", "reject"):
        raise PermissionDenied("You are not authorized to review this leave request.")
    with transaction.atomic():
        leave = get_object_or_404(
            LeaveRequest.objects.select_for_update(), pk=leave_id
        )
        if not (request.user.is_superuser or has_role(request.user, ROLE_HR)):
            manager = linked_employee(request.user)
            if not has_role(request.user, ROLE_MANAGER) or not manager or leave.employee.manager_id != manager.pk:
                raise PermissionDenied("Managers can review only their direct reports.")
        if leave.status != "pending":
            messages.error(request, "Only pending requests can be reviewed.")
            return redirect("leave_list")
        if decision == "approve":
            balance = LeaveBalance.objects.select_for_update().filter(
                employee=leave.employee, leave_type=leave.leave_type,
                year=leave.start_date.year,
            ).first()
            if balance and balance.remaining_days < leave.requested_days:
                messages.error(request, "Insufficient leave balance.")
                return redirect("leave_list")
            if balance:
                balance.used_days += leave.requested_days
                balance.save(update_fields=["used_days"])
            leave.status = "approved"
        else:
            leave.status = "rejected"
        leave.reviewer = request.user
        leave.review_note = request.POST.get("review_note", "")[:500]
        leave.reviewed_at = timezone.now()
        leave.save(update_fields=["status", "reviewer", "review_note", "reviewed_at"])
        audit(request, "leave." + decision, leave)
    messages.success(request, "Leave request " + decision + "d.")
    return redirect("leave_list")


@login_required
def payslip_list(request):
    employee = linked_employee(request.user)
    payroll = is_payroll_or_admin(request.user)
    if payroll:
        slips = Payslip.objects.select_related("employee")
    elif employee:
        slips = Payslip.objects.filter(employee=employee, published=True)
    else:
        raise PermissionDenied("Your login is not linked to an employee profile.")
    return render(request, "employees/payslips.html", {
        "payslips": slips, "can_manage_payroll": payroll,
    })


@login_required
def payslip_detail(request, payslip_id):
    slip = get_object_or_404(Payslip.objects.select_related("employee"), pk=payslip_id)
    own = linked_employee(request.user)
    if not (is_payroll_or_admin(request.user) or (
        slip.published and own and own.pk == slip.employee_id
    )):
        raise PermissionDenied("You are not authorized to view this payslip.")
    return render(request, "employees/payslip_detail.html", {"payslip": slip})


@login_required
@require_POST
def payslip_publish(request, payslip_id):
    if not is_payroll_or_admin(request.user):
        raise PermissionDenied("You are not authorized to publish payslips.")
    with transaction.atomic():
        slip = get_object_or_404(Payslip.objects.select_for_update(), pk=payslip_id)
        if not slip.published:
            slip.published = True
            slip.published_at = timezone.now()
            slip.save(update_fields=["published", "published_at"])
            audit(request, "payroll.payslip_published", slip)
    messages.success(request, "Payslip published.")
    return redirect("payslip_list")
