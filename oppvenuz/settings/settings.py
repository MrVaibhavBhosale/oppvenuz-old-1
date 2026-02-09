import os
from pathlib import Path
from datetime import timedelta
from decouple import config
import dj_database_url
from firebase_admin import initialize_app, credentials

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =========================
# SECURITY
# =========================
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]

# =========================
# APPS
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_yasg",
    "django_filters",
    "corsheaders",
    "phone_verify",
    "oauth2_provider",
    "social_django",
    "drf_social_oauth2",
    "rest_framework_social_oauth2",
    "fcm_django",
    "users.apps.UsersConfig",
    "service",
    "plan",
    "payment",
    "event_booking",
    "enquiry",
    "article",
    "e_invites",
    "pinterest",
    "feedbacks",
    "django_apscheduler",
    "documents",
    "content_manager",
    "seo",
]

AUTH_USER_MODEL = "users.CustomUser"

# =========================
# MIDDLEWARE
# =========================
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

# =========================
# DATABASE (Render)
# =========================
DATABASES = {
    "default": dj_database_url.parse(config("DATABASE_URL"))
}

# =========================
# STATIC
# =========================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =========================
# FIREBASE
# =========================
FCM_JSON = config("FCM_JSON_SDK")
cred = credentials.Certificate(FCM_JSON)
FIREBASE_APP = initialize_app(cred)

USER_FCM_JSON = config("USER_FCM_JSON_SDK")
new_cred = credentials.Certificate(USER_FCM_JSON)
FIREBASE_MESSAGING_APP = initialize_app(new_cred, name="user_app")

FCM_DJANGO_SETTINGS = {
    "DEFAULT_FIREBASE_APP": FIREBASE_APP,
    "ONE_DEVICE_PER_USER": True,
    "DELETE_INACTIVE_DEVICES": True,
}

# =========================
# EMAIL
# =========================
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# =========================
# PAYU
# =========================
PAYU_MERCHANT_KEY = config("PAYU_MERCHANT_KEY")
PAYU_MERCHANT_SALT = config("PAYU_MERCHANT_SALT")
PAYU_MODE = config("PAYU_MODE")

# =========================
# JWT
# =========================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(weeks=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=6),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =========================
# URLS
# =========================
ROOT_URLCONF = "oppvenuz.urls"
WSGI_APPLICATION = "oppvenuz.wsgi.application"

# =========================
# TEMPLATES
# =========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    },
]

# =========================
# PASSWORD VALIDATORS
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

# =========================
# LOGGING SAFE
# =========================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
}
