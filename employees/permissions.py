from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

ROLE_MANAGER = "Manager"
ROLE_HR = "HR"
ROLE_PAYROLL = "Payroll"

def has_role(user, *roles):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=roles).exists())

def linked_employee(user):
    try: return user.employee_profile
    except (AttributeError, user.__class__.DoesNotExist): return None

def role_required(*roles):
    def decorate(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not has_role(request.user, *roles): raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorate

def employee_or_role_allowed(user, employee, *roles):
    own = linked_employee(user)
    return user.is_superuser or has_role(user, *roles) or bool(own and own.pk == employee.pk)
