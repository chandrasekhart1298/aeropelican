
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("employees/", views.employee_directory, name="employee_directory"),
    path(
        "employees/<int:employee_id>/",
        views.employee_profile,
        name="employee_profile",
    ),
]
