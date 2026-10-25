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
    manager = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False, empty_label="No manager assigned")
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
            full_name=" ".join(part for part in (self.cleaned_data["first_name"].strip(), self.cleaned_data["last_name"].strip()) if part),
            work_email=self.cleaned_data["email"],
            department=self.cleaned_data["department"].strip(),
            job_title=self.cleaned_data["job_title"].strip(),
            joining_date=self.cleaned_data["joining_date"],
            manager=self.cleaned_data.get("manager"),
            is_active=True,
        )


class EmployeeManageForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False, label="Login username")
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    account_email = forms.EmailField(required=False, label="Login email")
    access_role = forms.ChoiceField(choices=ROLE_CHOICES, required=False, label="Portal role")
    login_enabled = forms.BooleanField(required=False, label="Allow this user to sign in")

    class Meta:
        model = Employee
        fields = ("employee_id", "full_name", "work_email", "department", "job_title", "joining_date", "manager", "is_active")
        widgets = {"joining_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, admin_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_mode = admin_mode
        self.fields["manager"].queryset = Employee.objects.filter(is_active=True).exclude(pk=self.instance.pk)
        if self.instance.user_id:
            user = self.instance.user
            self.fields["username"].initial = user.username
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["account_email"].initial = user.email
            self.fields["login_enabled"].initial = user.is_active
            self.fields["access_role"].initial = next(iter(user.groups.filter(name__in=[r[0] for r in ROLE_CHOICES]).values_list("name", flat=True)), "Employee")
        else:
            self.fields["login_enabled"].initial = False
        if not admin_mode:
            self.fields["access_role"].disabled = True
            self.fields["access_role"].help_text = "Only a system administrator can change portal roles."

    def clean_employee_id(self):
        value = self.cleaned_data["employee_id"].strip()
        qs = Employee.objects.filter(employee_id__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This employee ID is already in use.")
        return value

    def clean_work_email(self):
        value = self.cleaned_data["work_email"].strip().lower()
        qs = Employee.objects.filter(work_email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This work email is already in use.")
        return value

    def clean(self):
        data = super().clean()
        user = self.instance.user
        username = data.get("username", "").strip()
        account_email = data.get("account_email", "").strip().lower()
        if user and username and User.objects.filter(username__iexact=username).exclude(pk=user.pk).exists():
            self.add_error("username", "This username is already in use.")
        if user and account_email and User.objects.filter(email__iexact=account_email).exclude(pk=user.pk).exists():
            self.add_error("account_email", "This login email is already in use.")
        if not user and (username or account_email or data.get("login_enabled")):
            self.add_error(None, "This employee has no linked login. Create a login using the account creation workflow first.")
        if data.get("manager") and data["manager"].pk == self.instance.pk:
            self.add_error("manager", "An employee cannot be their own manager.")
        if user and user.is_superuser and not data.get("login_enabled") and not self.admin_mode:
            self.add_error("login_enabled", "Only a system administrator can change this account.")
        return data

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.full_name = " ".join(employee.full_name.split())
        if commit:
            employee.save()
            user = employee.user
            if user:
                user.username = self.cleaned_data.get("username", user.username).strip()
                user.first_name = self.cleaned_data.get("first_name", "").strip()
                user.last_name = self.cleaned_data.get("last_name", "").strip()
                user.email = self.cleaned_data.get("account_email", "").strip().lower()
                user.is_active = bool(self.cleaned_data.get("login_enabled")) and employee.is_active
                user.save()
                if self.admin_mode and not user.is_superuser:
                    user.groups.clear()
                    role, _ = __import__("django.contrib.auth.models", fromlist=["Group"]).Group.objects.get_or_create(
                        name=self.cleaned_data.get("access_role") or "Employee"
                    )
                    employee_group, _ = __import__("django.contrib.auth.models", fromlist=["Group"]).Group.objects.get_or_create(name="Employee")
                    user.groups.add(employee_group)
                    user.groups.add(role)
        return employee


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"}), "reason": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after start date.")
        if start and start < timezone.localdate():
            self.add_error("start_date", "Start date cannot be in the past.")
        return data
