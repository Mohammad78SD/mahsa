# Mahsa — HR & lunch management system

[![CI](https://github.com/Mohammad78SD/mahsa/actions/workflows/ci.yml/badge.svg)](https://github.com/Mohammad78SD/mahsa/actions/workflows/ci.yml)

Mahsa is a Django web application for managing day-to-day HR tasks in a small company: employee attendance, daily lunch reservations, SMS/OTP login, internal messaging with shared files, web-push notifications, surveys, monthly reports and payslips. The UI is Persian (RTL, Jalali calendar) and installable as a PWA.

## What it does

- **Authentication** — custom user model identified by phone number; password login with an SMS one-time-password (OTP) fallback and self-registration.
- **Lunch reservations** — employees reserve lunch per (Jalali) date; a view builds the next working day's list and sends it by SMS to configured recipients.
- **Attendance** — check-in/check-out records per user and day, fed by an RFID-reader JSON API; employees can file correction requests, which are listed and reviewed; attendance can be exported as an Excel report.
- **Messaging** — notifications shown in the app, plus file sharing between users (sender, recipients, "seen" tracking, download).
- **Web push** — browsers subscribe through a service worker; creating a notification pushes it to all subscribers using VAPID.
- **Surveys & reports** — a monthly report form, seasonal surveys (questions rated per season), and a view of the last report.
- **Payslips** — per-user payslip files, listed for the owning employee.
- **Employment letter** — generates a PNG employment form from user profile data using Pillow and a Persian font.
- **Admin** — Django admin for managing users, lunches, attendance, notifications, surveys and payslips.

## Tech stack

- Python, Django 5.0, SQLite (default)
- `django-jalali` / `jdatetime` for the Persian calendar
- `django-pwa` and a service worker for PWA support
- `pywebpush` / `py-vapid` for web push
- `ippanel` client for SMS
- Pillow, `arabic-reshaper`, `python-bidi` for Persian text rendering on images
- `openpyxl` for Excel reports
- `django-crispy-forms` (Bootstrap 4 pack), WhiteNoise for static files
- gunicorn + pm2 for deployment (`ecosystem.config.js`)

`requirements.txt` also lists Celery, django-celery-beat, django-apscheduler and Redis, which are not wired into `settings.py` in this repository; the lunch SMS endpoint is intended to be called by an external scheduler (e.g. cron).

## Architecture overview

| App | Responsibility | Key models |
| --- | --- | --- |
| `MetafanLunch/` | Project package: settings, root URLs, WSGI/ASGI | — |
| `lunch/` | Users, login/OTP, registration, lunch reservation, SMS helpers, employment letter | `CustomUser`, `Lunch`, `OTP` |
| `attendance/` | Attendance records, correction requests, RFID API, Excel export | `AttendaceRecord`, `AttendanceRequest` |
| `messaging/` | Notifications, web-push subscriptions and delivery (via `post_save` signal), shared files | `Notification`, `WebPushSubscription`, `SharedFile` |
| `surveys/` | Monthly reports, seasonal surveys, payslips | `MonthlyReport`, `Season`, `SeasonSurveyQuestion`, `SeasonSurveyResponse`, `Payslip` |
| `templates/` | Project-level HTML templates | — |
| `static/` | Project static assets (CSS, fonts, images, PWA icons) | — |

Main URL prefixes: `/panel/` (lunch, login, profile), `/attendance/`, `/messages/`, `/surveys/`, `/admin/`, plus `/save-subscription/` and `/get-vapid-key/` for web push.

## Getting started

Requires Python 3.12 or similar (the pinned dependencies do not build on very new Python versions) and the `fa_IR` locale is used if installed (optional).

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then edit values
set -a; source .env; set +a   # export the variables

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput   # production only
python manage.py runserver
```

For local development set `DJANGO_DEBUG=true`; this enables a throwaway secret key and serves uploaded media. In production `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` are required.

Generate a VAPID key pair for web push with `vapid --gen` (installed with `py-vapid`).

### Running with pm2

```bash
set -a; source .env; set +a
pm2 start ecosystem.config.js
```

This starts gunicorn on `$PORT` (default 8002).

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key (required unless `DJANGO_DEBUG=true`) |
| `DJANGO_DEBUG` | `true` for local development; default `false` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins including scheme |
| `DJANGO_CSRF_COOKIE_DOMAIN` | Optional CSRF cookie domain |
| `DJANGO_DB_PATH` | Optional SQLite file path (default `./db.sqlite3`) |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | Web-push VAPID key pair |
| `VAPID_ADMIN_EMAIL` | Contact address for the VAPID `mailto:` claim |
| `SMS_API_KEY` | ippanel API key |
| `SMS_SENDER` | Sender line number |
| `SMS_OTP_PATTERN` | ippanel pattern code for OTP messages |
| `SMS_LUNCH_PATTERN` | ippanel pattern code for the lunch list |
| `SMS_LUNCH_RECIPIENTS` | Comma-separated numbers that receive the lunch list |
| `LUNCH_EXTRA_NAMES`, `LUNCH_EXTRA_NAMES_NOT_SATURDAY`, `LUNCH_EXTRA_NAMES_SUN_TUE` | Optional comma-separated names appended to the lunch list for people without reservations (every day / all days except Saturday / Sunday and Tuesday only). Empty by default |
| `PORT` | gunicorn port under pm2 (default 8002) |

## Running tests

Tests use pytest with pytest-django, an in-memory SQLite database and dummy environment values (`MetafanLunch/test_settings.py`); the SMS client is mocked, so no real API is ever called. Use Python 3.12.

```bash
pip install -r requirements-dev.txt
pytest
```

The same command runs in GitHub Actions on every push and pull request (`.github/workflows/ci.yml`).

## Project structure

```
.
├── MetafanLunch/        # Django project (settings, urls, wsgi/asgi)
├── lunch/               # users, OTP login, lunch reservation, SMS helpers
├── attendance/          # attendance records, requests, RFID API
├── messaging/           # notifications, web push, shared files
├── surveys/             # monthly reports, seasonal surveys, payslips
├── templates/           # HTML templates
├── static/              # CSS, fonts, images, PWA icons
├── ecosystem.config.js  # pm2 process definition
├── .env.example         # environment variable template
├── manage.py
└── requirements.txt
```

## Screenshots

<!-- TODO: add screenshots (login, lunch reservation, attendance list, messages, monthly report). -->

## Security note

Secrets, databases, logs, uploaded media and collected static files are not tracked. Keep your real configuration in `.env` (git-ignored).
