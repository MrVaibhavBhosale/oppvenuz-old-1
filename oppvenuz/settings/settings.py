import os
from pathlib import Path
from decouple import config
from datetime import timedelta

# BASE_DIR FIRST
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR

# SECURITY - Render ready
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]

# ALL MISSING SETTINGS
STAGING_API_URL = config("STAGING_API_URL", default="https://staging.oppvenuz.com/api/")
PROD_API_URL = config("PROD_API_URL", default="https://www.oppvenuz.com/api/")
SOCIAL_AUTH_APPLE_ID_TEAM = config("SOCIAL_AUTH_APPLE_ID_TEAM", default="Y294V8N5W3")
VENDOR_FROM_EMAIL = config("VENDOR_FROM_EMAIL", default="vendor@oppvenuz.com")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# Apps (fcm_django comment out)
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth",
    "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "drf_yasg", "django_filters", "corsheaders",
    "phone_verify", "oauth2_provider", "social_django",
    "drf_social_oauth2", "rest_framework_social_oauth2",
    # "fcm_django",  # DISABLED for Render
    "users.apps.UsersConfig", "service", "plan", "payment",
    "event_booking", "enquiry", "article", "e_invites",
    "pinterest", "feedbacks", "django_apscheduler",
    "documents", "content_manager", "seo",
]

AUTH_USER_MODEL = "users.CustomUser"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    }
}

# Static Files - Render
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(weeks=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=6),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

ROOT_URLCONF = "oppvenuz.urls"
WSGI_APPLICATION = "oppvenuz.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

APSCHEDULER_AUTOSTART = True
