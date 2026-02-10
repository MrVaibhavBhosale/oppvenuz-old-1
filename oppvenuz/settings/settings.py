"""
Django settings for oppvenuz project - Render Production Ready
"""

import os
from datetime import timedelta
from decouple import config
from pathlib import Path


# BUILD PATHS FIRST - Render safe
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR

# SECURITY - Environment vars first
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]

# API URLS - All missing vars included
STAGING_API_URL = config("STAGING_API_URL", default="https://staging.oppvenuz.com/api/")
PROD_API_URL = config("PROD_API_URL", default="https://www.oppvenuz.com/api/")
SOCIAL_AUTH_APPLE_ID_TEAM = config("SOCIAL_AUTH_APPLE_ID_TEAM", default="Y294V8N5W3")
VENDOR_FROM_EMAIL = config("VENDOR_FROM_EMAIL", default="vendor@oppvenuz.com")


# Apps
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
    "service", "plan", "payment", "event_booking", "enquiry",
    "article", "e_invites", "pinterest", "feedbacks",
    "django_apscheduler", "documents", "content_manager", "seo",
]

AUTH_USER_MODEL = "users.CustomUser"

# Middleware - Render optimized
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Render static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework_social_oauth2.authentication.SocialAuthentication",
        "drf_social_oauth2.authentication.SocialAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "EXCEPTION_HANDLER": "users.utils.custom_exception_handler",
}

# Authentication Backends
AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookAppOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "rest_framework_social_oauth2.backends.DjangoOAuth2",
    "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.apple.AppleIdAuth",
    "users.backends.CaseInsensitiveEmailBackend",
)

# Social Auth Configs
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", default="")
SOCIAL_AUTH_FACEBOOK_KEY = config("SOCIAL_AUTH_FACEBOOK_KEY", default="")
SOCIAL_AUTH_FACEBOOK_SECRET = config("SOCIAL_AUTH_FACEBOOK_SECRET", default="")

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]

# Apple Social Auth
SOCIAL_AUTH_APPLE_ID_CLIENT = config("SOCIAL_AUTH_APPLE_ID_CLIENT")
SOCIAL_AUTH_APPLE_ID_TEAM = SOCIAL_AUTH_APPLE_ID_TEAM
SOCIAL_AUTH_APPLE_ID_KEY = config("SOCIAL_AUTH_APPLE_ID_KEY")
SOCIAL_AUTH_APPLE_ID_SECRET = config("SOCIAL_AUTH_APPLE_ID_SECRET")
SOCIAL_AUTH_APPLE_ID_SCOPE = ["email", "name"]
SOCIAL_AUTH_APPLE_ID_EMAIL_AS_USERNAME = True

# PayU
PAYU_MERCHANT_KEY = config("PAYU_MERCHANT_KEY")
PAYU_MERCHANT_SALT = config("PAYU_MERCHANT_SALT")
PAYU_MODE = config("PAYU_MODE")

# Phone Verification
PHONE_VERIFICATION = {
    "BACKEND": "phone_verify.backends.twilio.TwilioBackend",
    "OPTIONS": {
        "SID": config("TWILIO_SID", default="AC1a80f13412860cdcfe9d8612c316467b"),
        "SECRET": config("TWILIO_SECRET", default="b1e3f18e72c8500a924436b4d0bcc55c"),
        "FROM": config("TWILIO_FROM", default="+12289009622"),
        "SANDBOX_TOKEN": config("TWILIO_SANDBOX_TOKEN", default="123456"),
    },
    "TOKEN_LENGTH": 6,
    "MESSAGE": "Welcome to Oppvenuz! Please use security code {security_code} to proceed.",
    "APP_NAME": "Oppvenuz",
}

# FCM
FCM_DJANGO_SETTINGS = {
    "DEFAULT_FIREBASE_APP": FIREBASE_APP,
    "ONE_DEVICE_PER_USER": True,
    "DELETE_INACTIVE_DEVICES": True,
}

# Database - Render PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="dpg-d63cm624d50c73djnpg0-a.oregon-postgres.render.com"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Email
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(weeks=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=6),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# URLs & Templates
ROOT_URLCONF = "oppvenuz.urls"
WSGI_APPLICATION = "oppvenuz.wsgi.application"

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

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static Files - Render Optimized
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Production Settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False

# Logging - Render safe
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
    },
}

# APScheduler
APSCHEDULER_AUTOSTART = True
