from flask import (
    Blueprint,
    request,
    jsonify,
    session
)

from backend.common.responses import api_error

from backend.common.request_utils import get_json_body

from backend.common.authz import (
    login_required,
)

from backend.services.auth_service import authenticate_user
from backend.database.connection import get_db_connection


# =========================================================
# AUTH BLUEPRINT
# =========================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():
    """
    Kullanıcı girişi.

    POST /api/auth/login
    """

    data = get_json_body()

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    # -----------------------------------------------------
    # ZORUNLU ALAN KONTROLÜ
    # -----------------------------------------------------

    if not username or not password:

        return jsonify({
            "success": False,
            "error": (
                "Kullanıcı adı ve parola "
                "zorunludur."
            )
        }), 400

    # -----------------------------------------------------
    # KULLANICI DOĞRULAMA
    # -----------------------------------------------------

    user = authenticate_user(
        username,
        password
    )

    if not user:

        return jsonify({
            "success": False,
            "error": (
                "Kullanıcı adı veya parola "
                "hatalı."
            )
        }), 401

    # -----------------------------------------------------
    # FLASK SESSION
    # -----------------------------------------------------

    session["user_id"] = user["id"]

    session["username"] = (
        user["username"]
    )

    session["role"] = (
        user["role"]
    )

    session["department"] = (
        user["department"]
    )

    # -----------------------------------------------------
    # LOGIN AUDIT
    # -----------------------------------------------------

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO user_logins
            (
                user_id,
                ip_address,
                user_agent
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                user["id"],
                request.remote_addr,
                request.headers.get(
                    "User-Agent"
                ),
            ),
        )

        conn.commit()
        cur.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    # -----------------------------------------------------
    # FRONTEND'E KULLANICI BİLGİSİ
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "department": user["department"]
        }
    }), 200


# =========================================================
# MEVCUT OTURUMU GETİR
# =========================================================

@auth_bp.route(
    "/me",
    methods=["GET"]
)
def get_current_user():
    """
    Mevcut Flask session'ındaki kullanıcıyı döndürür.

    GET /api/auth/me
    """

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Oturum bulunamadı."
        }), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session["user_id"],
            "username": session.get(
                "username"
            ),
            "role": session.get(
                "role"
            ),
            "department": session.get(
                "department"
            )
        }
    }), 200


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route(
    "/logout",
    methods=["POST"],
)
def logout():
    session.clear()

    return jsonify({
        "success": True
    }), 200
