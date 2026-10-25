# AeroPeople — Employee Management Portal

Django-based employee self-service and HR workflow prototype.

## Current modules

- Individual sign-in using Django authentication and password hashing.
- HR/admin employee account creation that links a login to an employee profile; only superusers can assign HR, Manager, or Payroll groups.
- Role-aware employee directory and profile access.
- Employee attendance: Present/Clock In and Clock Out; server-recorded timestamps in Asia/Kolkata; personal history.
- HR/admin attendance report with employee and date filters.
- Leave requests, leave balance display, approvals, and manager direct-report scoping.
- Published payslips for employees and payroll access for authorized staff.
- Audit entries for important attendance, leave, account creation, and payroll actions.
- CSRF-protected forms and responsive templates.

## Roles

Create Django groups named exactly `Employee`, `Manager`, `HR`, and `Payroll`. The employee creation form assigns the Employee group automatically. HR/admin access is limited by server-side permission checks. An administrator account is not automatically an employee; to clock in, a user must be linked to an active Employee record.

## Windows setup / update

Back up `db.sqlite3` before updating. Do not delete the database.

```cmd
.venv\Scripts\activate
git pull origin feature/complete-hrms
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/accounts/login/ and sign in. Superusers can create employee accounts at `/employees/create/`; HR users with the HR group can also use this route. The form creates a Django login, hashes the password through Django's standard password system, links the user to the Employee record, and assigns the Employee group. Share initial passwords privately and encourage employees to change them after first sign-in.

## Important limitations

This is still a local learning prototype, not a production-ready HR/payroll system. Do not use real sensitive employee/payroll data or expose the development server publicly. Before production use, configure environment-based secrets, DEBUG=False, secure HTTPS/session settings, database backups, password reset and first-login password-change workflow, complete audit coverage, attendance correction/approval policy, and formal security review. SQLite and Django's development server are intended for local development. Payroll records do not implement Indian statutory tax, EPF, or ESI calculations.
