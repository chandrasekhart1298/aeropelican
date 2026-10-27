# Aeropelican Tech — HRMS

Aeropelican Tech is a Django-based employee services and HR workflow prototype. It includes employee account/profile management, attendance, leave requests and approvals, payslip visibility, role-based access controls, and read-only audit history.

> **Status:** development prototype. It is not production-ready. Do not store real employee, identity, banking, or payroll data in an exposed deployment.

## Features

- Django authentication and password hashing.
- Employee directory with search and active/inactive/all filters.
- HR/admin creation of employee accounts linked to employee profiles.
- Employee profile editing, login enable/disable, and employment status management.
- Role assignment restricted to system administrators; supported groups are `Employee`, `HR`, `Manager`, and `Payroll`.
- Attendance clock-in/clock-out with server-side timestamps and duplicate daily clock-in protection.
- HR/admin attendance report filters and recorded daily/monthly present/absent summary cards.
- Leave requests, weekday-based requested-day estimates (Monday–Friday; holidays are not yet excluded), balances, approval/rejection with review notes, and manager direct-report scoping.
- Payslip creation/editing for authorized payroll staff, optional PDF/JPEG/PNG attachments, protected document downloads, notes, publication controls, and employee-only visibility after publication.
- Searchable, paginated, read-only audit history for HR and system administrators.
- CSRF-protected forms, permission checks, responsive templates, and automated Django tests.
- GitHub Actions checks for migrations, Django system checks, and tests.

## Role and access notes

Django groups are used for portal roles. Only a superuser should grant privileged groups such as HR, Manager, or Payroll. A Django superuser is not automatically an employee; attendance self-service requires an active linked employee profile. Do not give the superuser login to ordinary staff.

Audit history displays events recorded by the application; it is not yet a complete tamper-proof compliance ledger, and some events do not include detailed before/after values.

## Local development on Windows

Open Git Bash or a terminal in the project directory. Back up `db.sqlite3` before updating, and never delete it just to resolve an environment issue.

### Update an existing checkout

```bash
git status --short
git switch feature/hrms-improvements
git pull --ff-only origin feature/hrms-improvements
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

If your local branch has uncommitted changes, inspect and back them up before switching branches or pulling. Do not blindly discard changes or apply old stashes.

### Fresh setup

```bash
git clone https://github.com/chandrasekhart1298/aeropelicantech.git
cd aeropelicantech
git switch feature/hrms-improvements
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py check
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/accounts/login/ and sign in with the superuser account you created. Keep credentials private. Employee accounts can be created through the People Operations controls. Share initial passwords securely and arrange password changes through a proper password-change/reset workflow before any real-world use.

## Main routes

- `/accounts/login/` — sign in
- `/` — dashboard
- `/employees/` — employee directory (HR/admin)
- `/employees/create/` — create linked employee login (HR/admin; privileged role assignment is admin-only)
- `/audit-history/` — searchable audit history (HR/admin)
- `/attendance/` — attendance
- `/leave/` — leave requests and reviews
- `/payroll/payslips/` — payslips and authorized payroll operations
- `/payroll/payslips/create/` — create a draft payslip (payroll/admin)
- `/payroll/payslips/<id>/edit/` — edit an unpublished draft (payroll/admin)
- `/admin/` — Django administration (superusers only)

## Git workflow

Work on `feature/hrms-improvements` until CI and local checks pass. Review the pull request into `master` before merging; do not push directly to `master` merely to synchronize branches. After an approved merge, update local `master` with a fast-forward pull. Never force-push shared branches to resolve divergence.

## Production readiness checklist

Before any production deployment:

- Set a strong secret via `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and restrictive `DJANGO_ALLOWED_HOSTS`.
- Use HTTPS, secure cookies, a supported production database, and managed secrets.
- Implement password reset, first-login password change, MFA/SSO policy, and account recovery.
- Complete audit coverage, restrict and protect audit records, and establish retention/monitoring policy.
- Define attendance correction and leave policy, statutory payroll calculations, payslip approvals, and reconciliation.
- Implement backup/restore testing, data retention, privacy controls, access reviews, and incident response.
- Run dependency/security checks, penetration testing, and a formal security review.
- Do not rely on SQLite or Django's development server for public production hosting.

Indian statutory payroll items such as income tax, EPF, and ESI are not calculated by this prototype.