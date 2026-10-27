from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from .models import AuditLog
from .permissions import ROLE_HR, has_role, linked_employee


@login_required
def audit_history(request):
    privileged = request.user.is_superuser or has_role(request.user, ROLE_HR)
    employee = linked_employee(request.user)
    if not privileged and not employee:
        raise PermissionDenied("Your login is not linked to an employee profile.")

    query = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    logs = AuditLog.objects.select_related("actor", "employee")
    if not privileged:
        logs = logs.filter(employee=employee)

    if query:
        logs = logs.filter(
            Q(action__icontains=query)
            | Q(object_type__icontains=query)
            | Q(object_id__icontains=query)
            | Q(actor__username__icontains=query)
        )
    if action:
        logs = logs.filter(action=action)

    actions = logs.order_by().values_list("action", flat=True).distinct()
    page = Paginator(logs, 50).get_page(request.GET.get("page"))
    return render(request, "employees/audit_history.html", {
        "page_obj": page,
        "query": query,
        "selected_action": action,
        "actions": actions,
        "is_privileged": privileged,
    })
