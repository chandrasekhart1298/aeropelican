from datetime import date
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from .models import Employee, Payslip

class AccessControlTests(TestCase):
    def setUp(self):
        self.employee_user = User.objects.create_user(username="employee", password="test-password-123")
        self.other_user = User.objects.create_user(username="other", password="test-password-123")
        self.hr_user = User.objects.create_user(username="hr", password="test-password-123")
        self.hr_user.groups.add(Group.objects.create(name="HR"))
        self.employee = Employee.objects.create(user=self.employee_user, employee_id="T001", full_name="Test One", work_email="one@example.test", department="Engineering", job_title="Developer", joining_date=date(2025,1,1))
        self.other = Employee.objects.create(user=self.other_user, employee_id="T002", full_name="Test Two", work_email="two@example.test", department="Sales", job_title="Analyst", joining_date=date(2025,2,1))
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
    def test_employee_cannot_open_other_profile(self):
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("employee_profile", args=[self.other.pk]))
        self.assertEqual(response.status_code, 403)
    def test_employee_can_open_own_profile(self):
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("employee_profile", args=[self.employee.pk]))
        self.assertEqual(response.status_code, 200)
    def test_employee_cannot_open_directory(self):
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(self.client.get(reverse("employee_directory")).status_code, 403)
    def test_hr_can_open_directory(self):
        self.client.login(username="hr", password="test-password-123")
        self.assertEqual(self.client.get(reverse("employee_directory")).status_code, 200)
    def test_unpublished_payslip_is_not_visible_to_employee(self):
        slip = Payslip.objects.create(employee=self.employee, period_start=date(2025,1,1), period_end=date(2025,1,31), basic_pay=50000)
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(self.client.get(reverse("payslip_detail", args=[slip.pk])).status_code, 403)
