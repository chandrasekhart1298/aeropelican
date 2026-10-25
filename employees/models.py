
from django.db import models


class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    work_email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    joining_date = models.DateField()

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"
