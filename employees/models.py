from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_profile")
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="direct_reports")
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    work_email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.employee_id} - {self.full_name}"

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        LATE = "late", "Late"
        ABSENT = "absent", "Absent"
        ON_LEAVE = "on_leave", "On leave"
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    work_date = models.DateField(default=timezone.localdate)
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField(max_length=250, blank=True)
    class Meta:
        ordering = ["-work_date", "-clock_in"]
        constraints = [models.UniqueConstraint(fields=["employee", "work_date"], name="unique_employee_attendance_day")]
    @property
    def duration_minutes(self):
        if not self.clock_in or not self.clock_out: return None
        return max(0, int((self.clock_out-self.clock_in).total_seconds() // 60))
    def __str__(self): return f"{self.employee} — {self.work_date}"

class LeaveBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.CharField(max_length=40, default="Annual")
    year = models.PositiveSmallIntegerField(default=timezone.localdate().year)
    entitled_days = models.DecimalField(max_digits=5, decimal_places=1, default=12, validators=[MinValueValidator(0)])
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0, validators=[MinValueValidator(0)])
    class Meta:
        constraints = [models.UniqueConstraint(fields=["employee", "leave_type", "year"], name="unique_employee_leave_balance_year")]
    @property
    def remaining_days(self): return self.entitled_days-self.used_days
    def __str__(self): return f"{self.employee} — {self.leave_type} ({self.year})"

class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.CharField(max_length=40, default="Annual")
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(max_length=1000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_leave_requests")
    review_note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ["-created_at"]
    @property
    def requested_days(self):
        if self.end_date < self.start_date: return 0
        days = 0
        current = self.start_date
        while current <= self.end_date:
            if current.weekday() < 5: days += 1
            current += timedelta(days=1)
        return days
    def __str__(self): return f"{self.employee} — {self.start_date} to {self.end_date}"

class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payslips")
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3, default="INR")
    basic_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    document = models.FileField(upload_to="payslips/%Y/%m/", blank=True, null=True)
    notes = models.CharField(max_length=500, blank=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-period_end"]
        constraints = [models.UniqueConstraint(fields=["employee", "period_start", "period_end"], name="unique_employee_payslip_period")]
    @property
    def gross_pay(self): return self.basic_pay+self.allowances
    @property
    def net_pay(self): return self.gross_pay-self.deductions
    def __str__(self): return f"{self.employee} — {self.period_start:%Y-%m}"

class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.created_at:%Y-%m-%d %H:%M} {self.action}"
