# AeroPeople — Employee Management Portal

AeroPeople is a Django-based employee management portal prototype built to practise real-world web application development.

## Project Goals

The goal is to build a simple, organized portal for viewing employee information and managing employee records.

## Technology Stack

- **Language:** Python
- **Web Framework:** Django
- **Database:** SQLite
- **Frontend:** HTML and CSS
- **Version Control:** Git and GitHub

## Current Features

- Employee portal home page
- Login and logout
- Employee directory
- Search employees by ID, name, or work email
- Employee profile page
- Django admin panel for managing employee records
- Database models for employee information

## Project Structure

```text
AeroPeople/
├── config/                  # Django project configuration
├── employees/               # Employee application
│   ├── migrations/          # Database migrations
│   ├── templates/
│   │   ├── employees/       # Portal pages
│   │   └── registration/    # Login page
│   ├── models.py            # Employee database model
│   ├── views.py             # Application views
│   ├── urls.py              # Application routes
│   └── admin.py             # Django admin configuration
├── .gitignore               # Files excluded from Git
├── manage.py                # Django management command
└── README.md                # Project documentation
```

## Run Locally on Windows

### 1. Clone the repository

```bash
git clone https://github.com/chandrasekhart1298/aeropelican.git
cd aeropelican
```

### 2. Create and activate a virtual environment

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Django

```bash
python -m pip install "Django==6.1.2"
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create an administrator account

```bash
python manage.py createsuperuser
```

Follow the prompts to create your own local administrator account.

### 6. Start the development server

```bash
python manage.py runserver
```

Open these addresses in your browser:

- Portal: http://127.0.0.1:8000/
- Employee directory: http://127.0.0.1:8000/employees/
- Admin panel: http://127.0.0.1:8000/admin/

## Planned Improvements

- Improve the portal's visual design
- Add employee creation, editing, and deletion
- Add role-based permissions
- Add employee attendance management
- Add leave request management
- Add dashboard statistics
- Add automated tests
- Prepare secure deployment configuration

## Development Status

**Status:** Work in progress

This is a learning and development prototype. Use fictional test data only. It is not yet approved or configured for production use with real company employee information.

## Author

**Chandrasekhar Thammisetty**

GitHub: https://github.com/ChandrasekharThammisetty2002

---

Built as a hands-on project to learn Django and employee portal development.
