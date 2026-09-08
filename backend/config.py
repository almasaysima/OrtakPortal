import os


def get_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def require_env(name):
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Zorunlu environment variable tanımlı değil: {name}"
        )

    return value.strip()


# =========================================================
# FLASK
# =========================================================

FLASK_SECRET_KEY = require_env(
    "FLASK_SECRET_KEY"
)

FLASK_DEBUG = get_bool(
    "FLASK_DEBUG",
    False
)


# =========================================================
# POSTGRESQL
# =========================================================

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "company-postgres"
)

POSTGRES_PORT = int(
    os.getenv(
        "POSTGRES_PORT",
        "5432"
    )
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "company_portal"
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "postgres"
)

POSTGRES_PASSWORD = require_env(
    "POSTGRES_PASSWORD"
)


# =========================================================
# REDIS
# =========================================================

REDIS_HOST = os.getenv(
    "REDIS_HOST",
    "company-redis"
)

REDIS_PORT = int(
    os.getenv(
        "REDIS_PORT",
        "6379"
    )
)


# =========================================================
# MINIO
# =========================================================

MINIO_ENDPOINT = os.getenv(
    "MINIO_ENDPOINT",
    "company-minio:9000"
)

MINIO_ACCESS_KEY = os.getenv(
    "MINIO_ACCESS_KEY",
    "companyadmin"
)

MINIO_SECRET_KEY = require_env(
    "MINIO_SECRET_KEY"
)

MINIO_BUCKET = os.getenv(
    "MINIO_BUCKET",
    "company-documents"
)


# =========================================================
# SMTP
# =========================================================

MAIL_HOST = os.getenv(
    "MAIL_HOST",
    "smtp.gmail.com"
)

MAIL_PORT = int(
    os.getenv(
        "MAIL_PORT",
        "587"
    )
)

MAIL_USERNAME = os.getenv(
    "MAIL_USERNAME",
    "testsirket0@gmail.com"
)

# Şifre sıfırlama kullanılmayacaksa boş bırakılabilir.
MAIL_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD",
    ""
)


# =========================================================
# INITIAL ADMIN
# =========================================================

INITIAL_ADMIN_USERNAME = os.getenv(
    "INITIAL_ADMIN_USERNAME",
    "admin"
)

INITIAL_ADMIN_PASSWORD = require_env(
    "INITIAL_ADMIN_PASSWORD"
)

INITIAL_ADMIN_EMAIL = os.getenv(
    "INITIAL_ADMIN_EMAIL",
    "admin@company.local"
)


# =========================================================
# ORGANIZATION
# =========================================================

ALLOWED_DEPARTMENTS = (
    "Bilgi Teknolojileri",
    "Finans",
    "İnsan Kaynakları",
)

# =========================================================
# LDAP / ACTIVE DIRECTORY
# =========================================================

LDAP_ENABLED = get_bool(
    "LDAP_ENABLED",
    False
)

LDAP_HOST = os.getenv(
    "LDAP_HOST",
    "192.168.10.10"
)

LDAP_PORT = int(
    os.getenv(
        "LDAP_PORT",
        "389"
    )
)

LDAP_DOMAIN = os.getenv(
    "LDAP_DOMAIN",
    "sirket.local"
)

LDAP_BASE_DN = os.getenv(
    "LDAP_BASE_DN",
    "DC=sirket,DC=local"
)
