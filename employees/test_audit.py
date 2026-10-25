from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import AuditLog


class AuditHistoryAccessTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="audit_employee", password="test-password-123"
        )
        self.hr = User.objects.create_user(
            username="audit_hr", password="test-password-123"
        )
        self.hr.groups.add(Group.objects.create(name="HR"))
        self.admin = User.objects.create_superuser(
            username="audit_admin", email="audit-admin@example.test",
            password="test-password-123",
        )
        AuditLog.objects.create(
            actor=self.hr, action="employee.profile_updated",
            object_type="Employee", object_id="42",
        )

    def test_employee_cannot_view_audit_history(self):
        self.client.login(username="audit_employee", password="test-password-123")
        self.assertEqual(self.client.get(reverse("audit_history")).status_code, 403)

    def test_hr_can_view_and_search_audit_history(self):
        self.client.login(username="audit_hr", password="test-password-123")
        response = self.client.get(reverse("audit_history"), {"q": "profile_updated"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "employee.profile_updated")

    def test_system_admin_can_view_audit_history(self):
        self.client.login(username="audit_admin", password="test-password-123")
        self.assertEqual(self.client.get(reverse("audit_history")).status_code, 200)
