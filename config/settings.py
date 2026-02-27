"""
Django settings for printshopmgr.

Uses django-environ for 12-factor configuration via .env file.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# Read .env file if it exists (dev convenience)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    # django-unfold must come before django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "storages",
    "django_celery_beat",
    # Local apps
    "accounts",
    "customers",
    "jobs",
    "payments",
    "documents",
    "production",
    "dashboard",
    "public",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database — PostgreSQL required for concurrent writes + SELECT FOR UPDATE
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://printshopmgr:devpassword@db:5432/printshopmgr")
}

# Custom User model (must be set before first migration)
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalisation — Thai locale
LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (user uploads: job artwork, proofs)
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login / logout
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Redis (Celery broker — Phase 2)
REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")

# Celery (Phase 2)
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

# LINE Messaging API (Phase 2)
LINE_CHANNEL_ACCESS_TOKEN = env("LINE_CHANNEL_ACCESS_TOKEN", default="")
LINE_CHANNEL_SECRET = env("LINE_CHANNEL_SECRET", default="")

# LINE Login OAuth (Phase 4 — staff LINE connect)
LINE_LOGIN_CHANNEL_ID = env("LINE_LOGIN_CHANNEL_ID", default="")
LINE_LOGIN_CHANNEL_SECRET = env("LINE_LOGIN_CHANNEL_SECRET", default="")

# Email (from .env, all optional — use console backend for local dev)
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@printshop.local")

# Base URL used in notification messages (e.g. tracking links in LINE messages)
BASE_URL = env("BASE_URL", default="http://localhost:8000")

# Celery Beat — use DB scheduler so schedules are editable from Django Admin
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "daily-summary": {
        "task": "notifications.tasks.send_daily_summary",
        "schedule": crontab(hour=8, minute=0),
    },
    "payment-reminders": {
        "task": "notifications.tasks.send_payment_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    "material-alerts": {
        "task": "notifications.tasks.send_material_alerts",
        "schedule": crontab(hour=9, minute=5),
    },
    "approval-reminders": {
        "task": "notifications.tasks.send_approval_reminders",
        "schedule": crontab(hour=10, minute=0),
    },
}

# django-unfold Admin customisation
UNFOLD = {
    "SITE_TITLE": "Print Shop Manager",
    "SITE_HEADER": "ระบบจัดการร้านพิมพ์",
    "SITE_SYMBOL": "print",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "ลูกค้า",
                "items": [
                    {"title": "ประเภทลูกค้า", "link": "/admin/customers/customertype/"},
                ],
            },
            {
                "title": "การผลิต",
                "items": [
                    {"title": "ประเภทสินค้า", "link": "/admin/production/producttype/"},
                    {"title": "วัสดุ", "link": "/admin/production/material/"},
                ],
            },
            {
                "title": "การเงิน",
                "items": [
                    {"title": "บัญชีธนาคาร", "link": "/admin/payments/bankaccount/"},
                ],
            },
            {
                "title": "ระบบ",
                "items": [
                    {"title": "ผู้ใช้งาน", "link": "/admin/accounts/user/"},
                    {"title": "ตั้งค่าระบบ", "link": "/admin/documents/setting/"},
                ],
            },
        ],
    },
}

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
