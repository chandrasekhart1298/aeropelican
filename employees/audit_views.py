from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q

from .models import AuditLog
from .permissions import ROLE_HR, has_role


@login_required
def audit_history(request):
    if not (request.user.is_superuser or has_role(request.user, ROLE_HR)):
        raise PermissionDenied("Only HR and system administrators can view audit history.")

    query = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    logs = AuditLog.objects.select_related("actor").all()

    if query:
        logs = logs.filter(
            Q(action__icontains=query)
            | Q(object_type__icontains=query)
            | Q(object_id__icontains=query)
            | Q(actor__username__icontains=query)
        )
    if action:
        logs = logs.filter(action=action)

    actions = (
        AuditLog.objects.order_by()
        .values_list("action", flat=True)
        .distinct()
    )
    page = Paginator(logs, 50).get_page(request.GET.get("page"))
    return render_audit_history(request, page, query, action, actions)


def render_audit_history(request, page, query, action, actions):
    from django.shortcuts import render

    return render(request, "employees/audit_history.html", {
        "page_obj": page,
        "query": query,
        "selected_action": action,
        "actions": actions,
    })
