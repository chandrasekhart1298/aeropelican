from datetime import date
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from .models import Attendance, Employee, Payslip


class AccessControlTests(TestCase):
    def setUp(self):
        self.employee_user = User.objects.create_user(
            username="employee", password="test-password-123"
        )
        self.other_user = User.objects.create_user(
            username="other", password="test-password-123"
        )
        self.hr_user = User.objects.create_user(
            username="hr", password="test-password-123"
        )
        self.hr_user.groups.add(Group.objects.create(name="HR"))
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.test",
            password="test-password-123",
        )
        self.employee = Employee.objects.create(
            user=self.employee_user, employee_id="T001",
            full_name="Test One", work_email="one@example.test",
            department="Engineering", job_title="Developer",
            joining_date=date(2025, 1, 1),
        )
        self.other = Employee.objects.create(
            user=self.other_user, employee_id="T002",
            full_name="Test Two", work_email="two@example.test",
            department="Sales", job_title="Analyst",
            joining_date=date(2025, 2, 1),
        )

    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)

    def test_employee_cannot_open_other_profile(self):
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("employee_profile", args=[self.other.pk]))
        self.assertEqual(response.status_code, 403)

    def test_employee_can_open_own_profile(self):
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(
            self.client.get(reverse("employee_profile", args=[self.employee.pk])).status_code,
            200,
        )

    def test_employee_cannot_open_directory(self):
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(self.client.get(reverse("employee_directory")).status_code, 403)

    def test_hr_can_open_directory(self):
        self.client.login(username="hr", password="test-password-123")
        self.assertEqual(self.client.get(reverse("employee_directory")).status_code, 200)

    def test_admin_can_open_attendance_without_employee_link(self):
        self.client.login(username="admin", password="test-password-123")
        self.assertEqual(self.client.get(reverse("attendance")).status_code, 200)

    def test_employee_can_clock_in_once_and_only_for_self(self):
        self.client.login(username="employee", password="test-password-123")
        response = self.client.post(reverse("clock_in"))
        self.assertEqual(response.status_code, 302)
        record = Attendance.objects.get(employee=self.employee)
        self.assertIsNotNone(record.clock_in)
        self.assertEqual(record.status, Attendance.Status.PRESENT)
        self.client.post(reverse("clock_in"))
        self.assertEqual(
            Attendance.objects.filter(employee=self.employee).count(), 1
        )
        self.assertFalse(Attendance.objects.filter(employee=self.other).exists())

    def test_admin_without_employee_link_cannot_clock_in_as_someone_else(self):
        self.client.login(username="admin", password="test-password-123")
        self.assertEqual(self.client.post(reverse("clock_in")).status_code, 403)
        self.assertFalse(Attendance.objects.exists())

    def _valid_employee_payload(self, **overrides):
        payload = {
            "username": "newstaff",
            "email": "newstaff@example.test",
            "first_name": "New",
            "last_name": "Staff",
            "employee_id": "T003",
            "department": "Engineering",
            "job_title": "Engineer",
            "joining_date": "2026-01-01",
            "manager": "",
            "password1": "SafeTestPassword#2026",
            "password2": "SafeTestPassword#2026",
            "access_role": "Employee",
        }
        payload.update(overrides)
        return payload

    def test_admin_can_create_linked_employee_login_and_assign_hr_role(self):
        self.client.login(username="admin", password="test-password-123")
        response = self.client.post(
            reverse("employee_create"),
            self._valid_employee_payload(
                username="newhr", email="newhr@example.test",
                employee_id="T003", access_role="HR",
            ),
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newhr")
        employee = Employee.objects.get(employee_id="T003")
        self.assertEqual(employee.user, user)
        self.assertTrue(user.check_password("SafeTestPassword#2026"))
        self.assertTrue(user.groups.filter(name="HR").exists())
        self.assertFalse(user.is_superuser)

    def test_hr_can_create_employee_but_cannot_assign_privileged_role(self):
        self.client.login(username="hr", password="test-password-123")
        response = self.client.post(
            reverse("employee_create"),
            self._valid_employee_payload(access_role="HR"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newstaff").exists())
        self.assertFalse(Employee.objects.filter(employee_id="T003").exists())

    def test_employee_cannot_create_user_login(self):
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("employee_create"))
        self.assertEqual(response.status_code, 403)

    def test_hr_sees_account_creation_navigation(self):
        self.client.login(username="hr", password="test-password-123")
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("employee_create"))

    def test_unpublished_payslip_is_not_visible_to_employee(self):
        slip = Payslip.objects.create(
            employee=self.employee, period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31), basic_pay=50000,
        )
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(
            self.client.get(reverse("payslip_detail", args=[slip.pk])).status_code,
            403,
        )
