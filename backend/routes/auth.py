import os
import ssl
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
)
from ldap3 import Server, Connection, Tls, MODIFY_REPLACE
from ldap3.utils.conv import escape_filter_chars
from werkzeug.security import generate_password_hash

from backend.common.responses import api_error
from backend.common.request_utils import get_json_body
from backend.common.authz import login_required
from backend.services.auth_service import authenticate_user
from backend.database.connection import get_db_connection
from backend.config import LDAP_DOMAIN

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

LOCK_SIGNALS = {}

def set_dc01_password(username, new_password):
    try:
        tls_config = Tls(validate=ssl.CERT_NONE)
        s = Server("192.168.10.10", port=636, use_ssl=True, tls=tls_config, connect_timeout=5)
        c = None
        for pw in ["ays'ma123", "aysima123", "Aysima123!"]:
            try:
                conn = Connection(s, user=f"Administrator@{LDAP_DOMAIN}", password=pw, auto_bind=True, receive_timeout=5)
                if conn.bound:
                    c = conn
                    break
            except Exception:
                continue
        if not c:
            print("DC01 LDAPS baglanamadi!")
            return False

        safe_u = escape_filter_chars(username)
        c.search("DC=sirket,DC=local", f"(sAMAccountName={safe_u})", attributes=["distinguishedName"])
        if c.entries:
            dn = c.entries[0].entry_dn
            unicode_pwd = ('"' + new_password + '"').encode("utf-16-le")
            c.modify(dn, {"unicodePwd": [(MODIFY_REPLACE, [unicode_pwd])]})
            print(f"DC01 Sifresi Degisti ({username}): {c.result.get('description')}")
            return c.result.get("description") == "success"
    except Exception as ex:
        print(f"DC01 Sifre Hatasi: {ex}")
    return False

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

    # 1. DC01 uzerinde Active Directory sifresini (Port 636 LDAPS) guncelle
    set_dc01_password(username, new_password)

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

    # 3. CLIENT01 bilgisayarini otomatik kilitlemesi icin sinyal ver
    LOCK_SIGNALS[username] = True

    return jsonify({
        "success": True,
        "message": "Parolaniz basariyla guncellendi! Windows oturumunuz kilitleniyor..."
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