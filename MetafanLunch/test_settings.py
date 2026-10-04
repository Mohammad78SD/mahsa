"""Test settings: dummy environment so tests never need real secrets or APIs."""
import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,127.0.0.1,localhost")
os.environ.setdefault("DJANGO_CSRF_TRUSTED_ORIGINS", "https://panel.example.com")
os.environ.setdefault("VAPID_PUBLIC_KEY", "dummy-public-key")
os.environ.setdefault("VAPID_PRIVATE_KEY", "dummy-private-key")
os.environ.setdefault("VAPID_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("SMS_API_KEY", "dummy-api-key")
os.environ.setdefault("SMS_SENDER", "+98000000000")
os.environ.setdefault("SMS_OTP_PATTERN", "dummy-otp-pattern")
os.environ.setdefault("SMS_LUNCH_PATTERN", "dummy-lunch-pattern")
os.environ.setdefault("SMS_LUNCH_RECIPIENTS", "09120000000,09120000001")

from MetafanLunch.settings import *  # noqa: E402,F401,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
