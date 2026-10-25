from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import LeaveRequestForm
from .models import Attendance, AuditLog, Employee, LeaveBalance, LeaveRequest, Payslip
from .permissions import ROLE_HR, ROLE_MANAGER, ROLE_PAYROLL, employee_or_role_allowed, has_role, linked_employee

def audit(request, action, obj):
    AuditLog.objects.create(actor=request.user, action=action, object_type=obj.__class__.__name__, object_id=str(obj.pk), ip_address=request.META.get("REMOTE_ADDR"))

@login_required
def home(request):
    employee = linked_employee(request.user)
    elevated = request.user.is_superuser or has_role(request.user, ROLE_HR, ROLE_MANAGER, ROLE_PAYROLL)
    ctx = {"employee":employee, "can_view_directory":request.user.is_superuser or has_role(request.user,ROLE_HR), "can_review_leave":request.user.is_superuser or has_role(request.user,ROLE_HR,ROLE_MANAGER), "can_manage_payroll":request.user.is_superuser or has_role(request.user,ROLE_PAYROLL)}
    if elevated:
        ctx["total_employees"] = Employee.objects.filter(is_active=True).count()
        ctx["pending_leave_count"] = LeaveRequest.objects.filter(status="pending").count()
    return render(request,"employees/home.html",ctx)

@login_required
def employee_directory(request):
    if not (request.user.is_superuser or has_role(request.user,ROLE_HR)): raise PermissionDenied
    query=request.GET.get("q","").strip()
    employees=Employee.objects.filter(is_active=True).order_by("employee_id")
    if query: employees=employees.filter(Q(employee_id__icontains=query)|Q(full_name__icontains=query)|Q(work_email__icontains=query)|Q(department__icontains=query)|Q(job_title__icontains=query))
    return render(request,"employees/directory.html",{"employees":employees,"query":query})

@login_required
def employee_profile(request,employee_id):
    employee=get_object_or_404(Employee,pk=employee_id,is_active=True)
    if not employee_or_role_allowed(request.user,employee,ROLE_HR): raise PermissionDenied
    return render(request,"employees/profile.html",{"employee":employee})

@login_required
def attendance(request):
    employee=linked_employee(request.user)
    if not employee: raise PermissionDenied("Your login is not linked to an employee profile. Contact HR.")
    record=Attendance.objects.filter(employee=employee,work_date=timezone.localdate()).first()
    return render(request,"employees/attendance.html",{"record":record,"history":Attendance.objects.filter(employee=employee)[:60]})

@login_required
@require_POST
def clock_in(request):
    employee=linked_employee(request.user)
    if not employee: raise PermissionDenied("Your login is not linked to an employee profile.")
    today=timezone.localdate()
    with transaction.atomic():
        record,created=Attendance.objects.get_or_create(employee=employee,work_date=today,defaults={"clock_in":timezone.now()})
        if not created:
            if record.clock_in:
                messages.error(request,"You have already clocked in today."); return redirect("attendance")
            record.clock_in=timezone.now(); record.save(update_fields=["clock_in"])
        audit(request,"attendance.clock_in",record)
    messages.success(request,"Clock-in recorded."); return redirect("attendance")

@login_required
@require_POST
def clock_out(request):
    employee=linked_employee(request.user)
    if not employee: raise PermissionDenied
    record=get_object_or_404(Attendance,employee=employee,work_date=timezone.localdate())
    if not record.clock_in or record.clock_out:
        messages.error(request,"You must clock in first and can only clock out once."); return redirect("attendance")
    record.clock_out=timezone.now(); record.save(update_fields=["clock_out"]); audit(request,"attendance.clock_out",record)
    messages.success(request,"Clock-out recorded."); return redirect("attendance")

@login_required
def leave_list(request):
    employee=linked_employee(request.user)
    reviewer=request.user.is_superuser or has_role(request.user,ROLE_HR,ROLE_MANAGER)
    if reviewer: requests=LeaveRequest.objects.select_related("employee","reviewer")
    elif employee: requests=LeaveRequest.objects.filter(employee=employee)
    else: raise PermissionDenied("Your login is not linked to an employee profile.")
    balances=LeaveBalance.objects.filter(employee=employee,year=timezone.localdate().year) if employee else []
    return render(request,"employees/leave_list.html",{"leave_requests":requests,"balances":balances,"can_review":reviewer})

@login_required
def leave_apply(request):
    employee=linked_employee(request.user)
    if not employee: raise PermissionDenied("Your login is not linked to an employee profile.")
    form=LeaveRequestForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        leave=form.save(commit=False); leave.employee=employee; leave.save(); audit(request,"leave.created",leave)
        messages.success(request,"Leave request submitted."); return redirect("leave_list")
    return render(request,"employees/leave_form.html",{"form":form})

@login_required
@require_POST
def leave_review(request,leave_id,decision):
    if not (request.user.is_superuser or has_role(request.user,ROLE_HR,ROLE_MANAGER)): raise PermissionDenied
    if decision not in ("approve","reject"): raise PermissionDenied
    with transaction.atomic():
        leave=get_object_or_404(LeaveRequest.objects.select_for_update(),pk=leave_id)
        if leave.status!="pending":
            messages.error(request,"Only pending requests can be reviewed."); return redirect("leave_list")
        if decision=="approve":
            balance=LeaveBalance.objects.select_for_update().filter(employee=leave.employee,leave_type=leave.leave_type,year=leave.start_date.year).first()
            if balance and balance.remaining_days < leave.requested_days:
                messages.error(request,"Insufficient leave balance."); return redirect("leave_list")
            if balance: balance.used_days+=leave.requested_days; balance.save(update_fields=["used_days"])
            leave.status="approved"
        else: leave.status="rejected"
        leave.reviewer=request.user; leave.review_note=request.POST.get("review_note","")[:500]; leave.reviewed_at=timezone.now()
        leave.save(update_fields=["status","reviewer","review_note","reviewed_at"]); audit(request,"leave."+decision,leave)
    messages.success(request,"Leave request "+decision+"d."); return redirect("leave_list")

@login_required
def payslip_list(request):
    employee=linked_employee(request.user); payroll=request.user.is_superuser or has_role(request.user,ROLE_PAYROLL)
    if payroll: slips=Payslip.objects.select_related("employee")
    elif employee: slips=Payslip.objects.filter(employee=employee,published=True)
    else: raise PermissionDenied("Your login is not linked to an employee profile.")
    return render(request,"employees/payslips.html",{"payslips":slips,"can_manage_payroll":payroll})

@login_required
def payslip_detail(request,payslip_id):
    slip=get_object_or_404(Payslip.objects.select_related("employee"),pk=payslip_id)
    own=linked_employee(request.user)
    if not (request.user.is_superuser or has_role(request.user,ROLE_PAYROLL) or (slip.published and own and own.pk==slip.employee_id)): raise PermissionDenied
    return render(request,"employees/payslip_detail.html",{"payslip":slip})

@login_required
@require_POST
def payslip_publish(request,payslip_id):
    if not (request.user.is_superuser or has_role(request.user,ROLE_PAYROLL)): raise PermissionDenied
    slip=get_object_or_404(Payslip,pk=payslip_id); slip.published=True; slip.published_at=timezone.now()
    slip.save(update_fields=["published","published_at"]); audit(request,"payroll.payslip_published",slip)
    messages.success(request,"Payslip published."); return redirect("payslip_list")
