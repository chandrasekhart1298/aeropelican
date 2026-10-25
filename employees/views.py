
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Employee


def home(request):
    return render(request, "employees/home.html")


@login_required
def employee_directory(request):
    employees = Employee.objects.all().order_by("employee_id")
    query = request.GET.get("q", "").strip()

    if query:
        employees = employees.filter(
            models.Q(employee_id__icontains=query)
            | models.Q(full_name__icontains=query)
            | models.Q(work_email__icontains=query)
        )

    return render(
        request,
        "employees/directory.html",
        {"employees": employees, "query": query},
    )

@login_required
def employee_profile(request, employee_id):
    employee = Employee.objects.get(pk=employee_id)
    return render(
        request,
        "employees/profile.html",
        {"employee": employee},
    )
