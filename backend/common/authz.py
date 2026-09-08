from functools import wraps

from flask import session

from backend.common.responses import api_error


# =========================================================
# PORTAL ROLLERİ
# =========================================================

ADMIN_ROLE = "admin"

MANAGER_ROLES = {
    "it_admin",
    "finance_admin",
    "hr_admin",
}

CONTENT_MANAGER_ROLES = {
    ADMIN_ROLE,
    *MANAGER_ROLES,
}


# =========================================================
# LOGIN KONTROLÜ
# =========================================================

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            return api_error(
                "Oturum açmanız gerekiyor.",
                401,
            )

        return view_func(
            *args,
            **kwargs
        )

    return wrapped


# =========================================================
# ROL KONTROLÜ
# =========================================================

def roles_required(*allowed_roles):
    def decorator(view_func):

        @wraps(view_func)
        def wrapped(*args, **kwargs):

            if "user_id" not in session:
                return api_error(
                    "Oturum açmanız gerekiyor.",
                    401,
                )

            role = str(
                session.get(
                    "role",
                    ""
                )
            ).lower()

            if role not in allowed_roles:
                return api_error(
                    "Bu işlem için yetkiniz yok.",
                    403,
                )

            return view_func(
                *args,
                **kwargs
            )

        return wrapped

    return decorator


# =========================================================
# YÖNETİCİ KONTROLLERİ
# =========================================================

def is_general_admin():
    return (
        str(
            session.get(
                "role",
                ""
            )
        ).lower()
        == ADMIN_ROLE
    )


def is_department_manager():
    role = str(
        session.get(
            "role",
            ""
        )
    ).lower()

    return role in MANAGER_ROLES


def can_manage_content():
    role = str(
        session.get(
            "role",
            ""
        )
    ).lower()

    return role in CONTENT_MANAGER_ROLES


# =========================================================
# DEPARTMAN YETKİSİ
# =========================================================

def get_content_department(
    requested_department=None
):
    """
    Genel admin:
        İstenen departmanı kullanabilir.

    Departman yöneticisi:
        Her zaman kendi departmanını kullanır.

    Çalışan:
        None döner.
    """

    if is_general_admin():

        department = str(
            requested_department
            or "Genel"
        ).strip()

        return (
            department
            or "Genel"
        )

    if is_department_manager():

        department = str(
            session.get(
                "department",
                ""
            )
        ).strip()

        return (
            department
            if department
            else None
        )

    return None


def can_manage_department(
    department
):
    """
    Kullanıcının belirli bir departmana ait
    içeriği yönetip yönetemeyeceğini kontrol eder.
    """

    if is_general_admin():
        return True

    if not is_department_manager():
        return False

    user_department = str(
        session.get(
            "department",
            ""
        )
    ).strip()

    content_department = str(
        department
        or ""
    ).strip()

    return (
        user_department
        == content_department
    )
