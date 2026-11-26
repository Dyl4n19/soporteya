import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "soporte",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "soporteya_project.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "soporteya_project.wsgi.application"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"},
}

BUSINESS_DB_ENGINE = os.getenv("BUSINESS_DB_ENGINE", "oracle").lower()
if BUSINESS_DB_ENGINE == "sqlite":
    DATABASES["negocio"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "negocio.sqlite3",
    }
    BUSINESS_MODELS_MANAGED = True
else:
    DATABASES["negocio"] = {
        "ENGINE": "django.db.backends.oracle",
        "NAME": os.getenv("ORACLE_DSN", ""),
        "USER": os.getenv("ORACLE_USER", ""),
        "PASSWORD": os.getenv("ORACLE_PASSWORD", ""),
        "OPTIONS": {},
    }
    BUSINESS_MODELS_MANAGED = False

DATABASE_ROUTERS = ["soporteya_project.routers.BusinessRouter"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "soporte.adapters.api.authentication.CookieTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "soporte.adapters.api.pagination.ApiPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "soporte.adapters.api.exceptions.uniform_exception_handler",
}

CORS_ALLOWED_ORIGINS = [os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")]
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r"^/api/.*$"
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
TOKEN_COOKIE_NAME = "soporteya_token"
TOKEN_COOKIE_SECURE = os.getenv("TOKEN_COOKIE_SECURE", "False").lower() == "true"
TOKEN_COOKIE_SAMESITE = "Lax"

