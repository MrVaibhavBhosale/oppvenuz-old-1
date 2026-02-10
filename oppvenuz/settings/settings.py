import os
from datetime import timedelta
from pathlib import Path
from decouple import config


# --------------------------------------------------
# BASE DIR
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = BASE_DIR

# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
    "api.oppvenuz.com",
    "staging.oppvenuz.com",
]

CORS_ORIGIN_ALLOW_ALL = True

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_yasg",

    "oauth2_provider",
    "social_django",
    "drf_social_oauth2",
    "rest_framework_social_oauth2",

    # project apps
    "users",
    "service",
    "plan",
    "payment",
    "event_booking",
    "enquiry",
    "article",
    "e_invites",
    "pinterest",
    "feedbacks",
    "documents",
    "content_manager",
    "seo",
]

AUTH_USER_MODEL = "users.CustomUser"

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

# --------------------------------------------------
# REST FRAMEWORK
# --------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "EXCEPTION_HANDLER": "users.utils.custom_exception_handler",
}

# --------------------------------------------------
# DATABASE (Render PostgreSQL)
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", cast=int),
    }
}

# --------------------------------------------------
# JWT
# --------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=35),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

ROOT_URLCONF = "oppvenuz.urls"
WSGI_APPLICATION = "oppvenuz.wsgi.application"

# --------------------------------------------------
# STATIC FILES (Render)
# --------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# --------------------------------------------------
# TIMEZONE
# --------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# EMAIL
# --------------------------------------------------
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# --------------------------------------------------
# AWS S3 (optional – env based)
# --------------------------------------------------
AWS_ACCESS_KEY_ID = config("s3AccessKey", default=None)
AWS_SECRET_ACCESS_KEY = config("s3Secret", default=None)
AWS_STORAGE_BUCKET_NAME = config("S3_BUCKET_NAME", default=None)
AWS_S3_REGION_NAME = "ap-south-1"

# --------------------------------------------------
# PROJECT / INTERNAL TOKENS
# --------------------------------------------------
CLIENT_ID = config("CLIENT_ID", default=None)
BASIC_TOKEN = config("BASIC_TOKEN", default=None)
PROJECT_ID = config("PROJECT_ID", default=None)

DEVELOP_BRANCH_API_KEY = config("DEVELOP_BRANCH_API_KEY", default=None)
STAGING_BRANCH_API_KEY = config("STAGING_BRANCH_API_KEY", default=None)

# --------------------------------------------------
# PLACID (E-Invite / Image generation)
# --------------------------------------------------
PLACID_TEMPLATE_URL = config("PLACID_TEMPLATE_URL", default=None)
EINVITE_BEARER_TOKEN = config("EINVITE_BEARER_TOKEN", default=None)

# --------------------------------------------------
# SIGNDESK (KYC / Agreement)
# --------------------------------------------------
SIGNDESK_API_KEY = config("SIGNDESK_API_KEY", default=None)
SIGNDESK_APPLICATION_ID = config("SIGNDESK_APPLICATION_ID", default=None)

PHONE_VERIFICATION = {
    "BACKEND": "phone_verify.backends.base.BaseBackend",
}

# --------------------------------------------------
# TEXT LOCAL / SMS
# --------------------------------------------------
TEXT_LOCAL_API_KEY = config("TEXT_LOCAL_API_KEY", default=None)

# --------------------------------------------------
# APPLE / SUBSCRIPTION / OPTIONAL
# --------------------------------------------------
OPTIONAL_SHARED_SECRET = config("OPTIONAL_SHARED_SECRET", default=None)

# --------------------------------------------------
# SOCIAL AUTH
# --------------------------------------------------
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", default="")

SOCIAL_AUTH_FACEBOOK_KEY = config("SOCIAL_AUTH_FACEBOOK_KEY", default="")
SOCIAL_AUTH_FACEBOOK_SECRET = config("SOCIAL_AUTH_FACEBOOK_SECRET", default="")

# --------------------------------------------------
# LOGGING (Render safe – console)
# --------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
