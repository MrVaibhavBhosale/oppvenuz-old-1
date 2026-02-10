"""
oppvenuz - Render Production Ready - ALL ERRORS FIXED
"""
import os
from pathlib import Path
from decouple import config
from datetime import timedelta

# 1. BASE_DIR FIRST
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR

# 2. SECURITY
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]

# 3. ALL REQUIRED SETTINGS (सर्व errors fix)
STAGING_API_URL = config("STAGING_API_URL", default="https://staging.oppvenuz.com/api/")
PROD_API_URL = config("PROD_API_URL", default="https://www.oppvenuz.com/api/")
SOCIAL_AUTH_APPLE_ID_TEAM = config("SOCIAL_AUTH_APPLE_ID_TEAM", default="Y294V8N5W3")
VENDOR_FROM_EMAIL = config("VENDOR_FROM_EMAIL", default="vendor@oppvenuz.com")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# 4. PHONE_VERIFICATION (सर्वात महत्वाचं!)
PHONE_VERIFICATION = {
    "BACKEND": "phone_verify.backends.twilio.TwilioBackend",
    "OPTIONS": {
        "SID": "AC1a80f13412860cdcfe9d8612c316467b",
        "SECRET": "b1e3f18e72c8500a924436b4d0bcc55c",
        "FROM": "+12289009622",
        "SANDBOX_TOKEN": "123456",
    },
    "TOKEN_LENGTH": 6,
    "MESSAGE": "Welcome to Oppvenuz! Please use security code {security_code}",
    "APP_NAME": "Oppvenuz",
    "SECURITY_CODE_EXPIRATION_TIME": 3600,
    "VERIFY_SECURITY_CODE_ONLY_ONCE": False,
}

# 5. Apps (fcm_django हटवलं)
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
    "users.apps.UsersConfig",
    "service", "plan", "payment", "event_booking", 
    "enquiry", "article", "e_invites", "pinterest",
    "feedbacks", "django_apscheduler", "documents",
    "content_manager", "seo",
]

# 6. Custom User
AUTH_USER_MODEL = "users.CustomUser"

# 7. Middleware - Render Ready
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
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

# 8. REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework_social_oauth2.authentication.SocialAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

# 9. Database - Render PostgreSQL
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

# 10. PayU Payment
PAYU_MERCHANT_KEY = config("PAYU_MERCHANT_KEY")
PAYU_MERCHANT_SALT = config("PAYU_MERCHANT_SALT")
PAYU_MODE = config("PAYU_MODE")

# 11. JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(weeks=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=6),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# 12. Static Files - Render Optimized
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 13. Templates
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

# 14. Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# 15. Production Settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
APSCHEDULER_AUTOSTART = True
