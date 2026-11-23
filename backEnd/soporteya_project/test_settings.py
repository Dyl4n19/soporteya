from .settings import *


DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    "negocio": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
BUSINESS_DB_ENGINE = "sqlite"
BUSINESS_MODELS_MANAGED = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
