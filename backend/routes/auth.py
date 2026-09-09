import os
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
)
from ldap3 import Server, Connection, MODIFY_REPLACE, SUBTREE
from ldap3.utils.conv import escape_filter_chars
from werkzeug.security import generate_password_hash

from backend.common.responses import api_error
from backend.common.request_utils import get_json_body
from backend.common.authz import login_required
from backend.services.auth_service import authenticate_user
from backend.database.connection import get_db_connection
from backend.config import (
    LDAP_HOST,
    LDAP_PORT,
    LDAP_DOMAIN,
    LDAP_BASE_DN,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

LOCK_SIGNALS = {}

def set_dc01_ad_password(username, new_password):
    try:
        server = Server("192.168.10.10", port=389, connect_timeout=5)
        admin_conn = Connection(
            server,
            user=f"Administrator@{LDAP_DOMAIN}",
            password=os.getenv("LDAP_ADMIN_PASSWORD", "aysima123"),
            auto_bind=True,
            receive_timeout=5,
        )
        if admin_conn.bound:
            safe_u = escape_filter_chars(username)
            admin_conn.search(
                search_base="DC=sirket,DC=local",
                search_filter=f"(sAMAccountName={safe_u})",
                search_scope=SUBTREE,
                attributes=["entryDN"],
            )
            if admin_conn.entries:
                user_dn = admin_conn.entries[0].entry_dn
                unicode_pass = ('"' + new_password + '"').encode("utf-16-le")
                admin_conn.modify(
                    user_dn, {"unicodePwd": [(MODIFY_REPLACE, [unicode_pass])]}
                )
                print(f"DC01 Sifresi Degisti ({username}): {admin_conn.result.get('description')}")
                return admin_conn.result.get("description") == "success"
    except Exception as ex:
        print(f"DC01 Sifre Guncelleme Hatasi: {ex}")
    return False

def trigger_user_lock(username):
    LOCK_SIGNALS[username] = True

@auth_bp.route("/check-lock", methods=["GET"])
def check_lock():
    username = request.args.get("username", "")
    should_lock = LOCK_SIGNALS.pop(username, False)
    return jsonify({"lock": should_lock})

@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Oturum bulunamadi."}), 401

    data = get_json_body()
    new_password = str(data.get("new_password", "")).strip()

    if not new_password or len(new_password) < 6:
        return jsonify({"success": False, "error": "Yeni parola en az 6 karakter olmalidir."}), 400

    username = session.get("username")
    user_id = session.get("user_id")

    # 1. DC01 uzerinde Active Directory sifresini guncelle
    set_dc01_ad_password(username, new_password)

    # 2. PostgreSQL veritabaninda guncelle
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (generate_password_hash(new_password), user_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()

    # 3. Bilgisayari otomatik kilitlemek icin sinyal ver
    trigger_user_lock(username)

    return jsonify({
        "success": True,
        "message": "Parolaniz Active Directory (DC01) ve portal uzerinde basariyla guncellendi! Bilgisayariniz kilitleniyor..."
    }), 200

@auth_bp.route("/login", methods=["POST"])
def login():
    data = get_json_body()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({"success": False, "error": "Kullanici adi ve parola zorunludur."}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"success": False, "error": "Kullanici adi veya parola hatali."}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["department"] = user["department"]

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO user_logins (user_id, ip_address, user_agent)
            VALUES (%s, %s, %s)
            """,
            (user["id"], request.remote_addr, request.headers.get("User-Agent")),
        )
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "department": user["department"],
        },
    }), 200

@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Oturum bulunamadi."}), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session["user_id"],
            "username": session.get("username"),
            "role": session.get("role"),
            "department": session.get("department"),
        },
    }), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True}), 200