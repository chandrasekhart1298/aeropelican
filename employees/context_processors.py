from .permissions import ROLE_HR, ROLE_MANAGER, ROLE_PAYROLL, has_role


def portal_permissions(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"can_manage_employee_accounts": False, "is_hr_or_admin": False}
    admin_or_hr = user.is_superuser or has_role(user, ROLE_HR)
    return {
        "can_manage_employee_accounts": admin_or_hr,
        "is_hr_or_admin": admin_or_hr,
        "is_manager": has_role(user, ROLE_MANAGER),
        "is_payroll": has_role(user, ROLE_PAYROLL),
    }
