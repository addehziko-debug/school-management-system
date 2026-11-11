# School Management System

A Django-based school portal for managing departments, courses, students, attendance, assignments, and student submissions. It includes a staff-facing portal, a student workspace, and a REST API.

## Features

- Browse the portal and department directory.
- Manage departments, courses, and student records.
- Record attendance and publish assignments.
- Let students view assignments and submit work.
- Review and download submissions through staff endpoints.
- Manage homepage flyers and background images.
- Sign up, sign in, and authenticate API requests with tokens.
- Store student submissions separately from public media files.

## Technology

- Python
- Django 6.1.3
- Django REST framework 3.18.3
- SQLite for local development

## Getting started

The Django project is in the `school/` directory. From the repository root, create and activate a virtual environment, then install the application dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install Django==6.1.3 djangorestframework==3.18.3
```

On macOS or Linux, activate the environment with:

```sh
source .venv/bin/activate
```

Run the following commands from the `school/` directory:

```sh
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [http://127.0.0.1:8000/portal/](http://127.0.0.1:8000/portal/) for the portal. The Django admin is available at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

## Routes

| Route | Purpose |
| --- | --- |
| `/portal/` | Main portal |
| `/portal/departments/` | Department directory |
| `/portal/student/` | Student workspace |
| `/portal/student/profile/` | Student profile API |
| `/portal/student/assignments/` | Student assignments API |
| `/portal/student/submissions/` | Student submissions API |
| `/portal/staff/submissions/` | Staff submissions API |
| `/portal/attendance/` | Attendance API |
| `/portal/assignments/` | Assignments API |
| `/auth/create/` | Create an account and receive an API token |
| `/auth/login/` | Sign in and receive an API token |
| `/auth/logout/` | Revoke the authenticated API token |
| `/auth/me/` | Get the authenticated user's staff status |

The authentication endpoints accept JSON. For example, sign in with:

```json
{
  "username": "your-username",
  "password": "your-password"
}
```

For token-authenticated API requests, send the returned token in the `Authorization` header:

```text
Authorization: Token your-token
```

## Tests

From the `school/` directory, run the Django test suite:

```sh
python manage.py test
```

## Development and deployment notes

The checked-in settings use SQLite, enable Django debug mode, and send email to the console. They are intended for local development, not public deployment. Before deploying, configure a production-only secret through `DJANGO_SECRET_KEY`, disable debug mode, set `ALLOWED_HOSTS`, and configure production-appropriate database, email, static-file, and media storage settings. Keep secrets and local databases out of version control.
