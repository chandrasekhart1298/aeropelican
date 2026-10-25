from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Employee, LeaveRequest

User = get_user_model()
ROLE_CHOICES = (
    ("Employee", "Employee"),
    ("HR", "HR"),
    ("Manager", "Manager"),
    ("Payroll", "Payroll"),
)


class EmployeeAccountForm(UserCreationForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(label="Work email")
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name", required=False)
    employee_id = forms.CharField(max_length=20)
    department = forms.CharField(max_length=100)
    job_title = forms.CharField(max_length=100)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    manager = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="No manager assigned",
    )
    access_role = forms.ChoiceField(choices=ROLE_CHOICES, initial="Employee", label="Portal role")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, admin_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_mode = admin_mode
        if not admin_mode:
            self.fields["access_role"].choices = (("Employee", "Employee"),)
            self.fields["access_role"].initial = "Employee"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address.")
        if Employee.objects.filter(work_email__iexact=email).exists():
            raise forms.ValidationError("An employee already uses this work email.")
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data["employee_id"].strip()
        if Employee.objects.filter(employee_id__iexact=employee_id).exists():
            raise forms.ValidationError("This employee ID already exists.")
        return employee_id

    def save_user(self):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = True
        user.save()
        return user

    def save_employee(self, user):
        return Employee.objects.create(
            user=user,
            employee_id=self.cleaned_data["employee_id"].strip(),
            full_name=" ".join(part for part in (
                self.cleaned_data["first_name"].strip(),
                self.cleaned_data["last_name"].strip(),
            ) if part),
            work_email=self.cleaned_data["email"],
            department=self.cleaned_data["department"].strip(),
            job_title=self.cleaned_data["job_title"].strip(),
            joining_date=self.cleaned_data["joining_date"],
            manager=self.cleaned_data.get("manager"),
            is_active=True,
        )


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after start date.")
        if start and start < timezone.localdate():
            self.add_error("start_date", "Start date cannot be in the past.")
        return data
