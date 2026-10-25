# AeroPeople — Employee Management Portal

Django-based employee self-service and HR workflow learning prototype.

## Modules in this branch

- Login-protected dashboard and employee account linking
- Employee directory restricted to HR and superusers
- Employee profiles with owner-only access unless HR/admin
- Attendance clock-in/out and personal history
- Leave requests, reviewer decisions, and leave balances
- Payslip records, employee access to published payslips, payroll publishing
- Audit entries for key portal actions
- CSRF-protected forms and responsive HTML templates
- Django admin interface intended for superuser-only access

## Role setup

Create Django Groups named exactly Employee, Manager, HR, and Payroll and assign users through the admin. Superusers have full portal access. Employee accounts must be explicitly linked to the matching Employee row.

- Employee: own profile, attendance, leave, published payslips.
- Manager: leave review permission in this prototype. Team-only scoping is not yet implemented; review access is organization-wide, so do not use with real employee records.
- HR: employee directory/profiles and leave review.
- Payroll: payslip listing and publishing.
- Superuser: full administrative access and account linking.

## Setup (Windows)

Back up your local db.sqlite3 first. This branch adds a migration and does not ask you to delete the database.

    .venv\\Scripts\\activate
    python manage.py migrate
    python manage.py check
    python manage.py test
    python manage.py runserver

If cloning without a virtual environment, create one and install Django 6.1.2 first. Open http://127.0.0.1:8000/ and sign in. Use /admin/ to create groups, accounts, employee records, leave balances and payslips. Assign the correct user link on each Employee record.

## Prototype limitations

This is not a production HR/payroll system. Before real use, implement manager/team scoping, robust leave balance handling for overlapping requests and partial days, attendance policies and anti-tampering controls, complete audit coverage, deployment secrets/security, backups, and automated end-to-end tests. Payroll amounts are stored but Indian statutory tax/EPF/ESI calculations are not implemented. SQLite and Django's development server are for local development only. Use fictional data while learning.
