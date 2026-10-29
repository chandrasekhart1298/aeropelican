from datetime import date
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from .models import Attendance, AuditLog, Employee, LeaveRequest, Payslip


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


    def test_hr_can_edit_employee_details_but_not_assign_roles(self):
        self.client.login(username="hr", password="test-password-123")
        response = self.client.post(reverse("employee_manage", args=[self.employee.pk]), {
            "employee_id": "T001", "full_name": "Test One Updated",
            "work_email": "one@example.test", "department": "Platform",
            "job_title": "Senior Developer", "joining_date": "2025-01-01",
            "manager": "", "is_active": "on", "username": "employee",
            "first_name": "Test", "last_name": "One", "account_email": "one@example.test",
            "login_enabled": "on", "access_role": "HR",
        })
        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee.department, "Platform")
        self.assertFalse(self.employee_user.groups.filter(name="HR").exists())

    def test_employee_cannot_manage_an_employee_account(self):
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(self.client.get(reverse("employee_manage", args=[self.other.pk])).status_code, 403)

    def test_admin_can_open_employee_management_page(self):
        self.client.login(username="admin", password="test-password-123")
        self.assertEqual(self.client.get(reverse("employee_manage", args=[self.employee.pk])).status_code, 200)

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

    def test_employee_leave_list_contains_only_own_requests(self):
        LeaveRequest.objects.create(
            employee=self.employee, start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 3), reason="Personal",
        )
        LeaveRequest.objects.create(
            employee=self.other, start_date=date(2026, 11, 4),
            end_date=date(2026, 11, 5), reason="Other employee",
        )
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("leave_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test One")
        self.assertNotContains(response, "Test Two")

    def test_employee_payslip_list_shows_only_own_published_slips(self):
        own_slip = Payslip.objects.create(
            employee=self.employee, period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31), basic_pay=1000, published=True,
        )
        Payslip.objects.create(
            employee=self.other, period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31), basic_pay=2000, published=True,
        )
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("payslip_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("payslip_detail", args=[own_slip.pk]))
        other_slip = Payslip.objects.get(employee=self.other, period_start=date(2026, 1, 1))
        self.assertNotContains(response, reverse("payslip_detail", args=[other_slip.pk]))

    def test_employee_cannot_open_or_download_another_employees_payslip(self):
        slip = Payslip.objects.create(
            employee=self.other, period_start=date(2026, 2, 1),
            period_end=date(2026, 2, 28), basic_pay=2000, published=True,
        )
        self.client.login(username="employee", password="test-password-123")
        self.assertEqual(
            self.client.get(reverse("payslip_detail", args=[slip.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("payslip_document", args=[slip.pk])).status_code,
            403,
        )

    def test_employee_audit_history_is_limited_to_their_employee_profile(self):
        AuditLog.objects.create(
            employee=self.employee, actor=self.employee_user,
            action="own.activity", object_type="Attendance", object_id="1",
        )
        AuditLog.objects.create(
            employee=self.other, actor=self.other_user,
            action="other.secret_activity", object_type="Payslip", object_id="2",
        )
        self.client.login(username="employee", password="test-password-123")
        response = self.client.get(reverse("audit_history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "own.activity")
        self.assertNotContains(response, "other.secret_activity")

    def test_hr_audit_history_can_view_org_wide_events(self):
        AuditLog.objects.create(
            employee=self.employee, actor=self.employee_user,
            action="employee.activity", object_type="Attendance", object_id="1",
        )
        AuditLog.objects.create(
            employee=self.other, actor=self.other_user,
            action="other.activity", object_type="Payslip", object_id="2",
        )
        self.client.login(username="hr", password="test-password-123")
        response = self.client.get(reverse("audit_history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "employee.activity")
        self.assertContains(response, "other.activity")

    def test_manager_leave_list_is_limited_to_direct_reports(self):
        manager_user = User.objects.create_user(
            username="manager", password="test-password-123"
        )
        manager_group, _ = Group.objects.get_or_create(name="Manager")
        manager_user.groups.add(manager_group)
        manager_employee = Employee.objects.create(
            user=manager_user, employee_id="M001",
            full_name="Test Manager", work_email="manager@example.test",
            department="Engineering", job_title="Manager",
            joining_date=date(2024, 1, 1),
        )
        self.employee.manager = manager_employee
        self.employee.save(update_fields=["manager"])
        LeaveRequest.objects.create(
            employee=self.employee, start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 3), reason="Direct report leave",
        )
        LeaveRequest.objects.create(
            employee=self.other, start_date=date(2026, 11, 4),
            end_date=date(2026, 11, 5), reason="Unrelated leave",
        )
        self.client.login(username="manager", password="test-password-123")
        response = self.client.get(reverse("leave_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Direct report leave")
        self.assertNotContains(response, "Unrelated leave")

    def test_manager_without_linked_employee_sees_no_leave_requests(self):
        manager_user = User.objects.create_user(
            username="manager_unlinked", password="test-password-123"
        )
        manager_group, _ = Group.objects.get_or_create(name="Manager")
        manager_user.groups.add(manager_group)
        LeaveRequest.objects.create(
            employee=self.employee, start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 3), reason="Private leave request",
        )
        self.client.login(username="manager_unlinked", password="test-password-123")
        response = self.client.get(reverse("leave_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private leave request")

