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


# =========================================================
# SIFRE DEGISTIRME VE ACTIVE DIRECTORY SENKRONIZASYONU
# =========================================================

import os
from ldap3 import Server, Connection, MODIFY_REPLACE, SUBTREE
from ldap3.utils.conv import escape_filter_chars
from werkzeug.security import generate_password_hash
from backend.config import LDAP_HOST, LDAP_PORT, LDAP_DOMAIN, LDAP_BASE_DN

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Oturum bulunamadi.'}), 401

    data = get_json_body()
    new_password = str(data.get('new_password', '')).strip()

    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Yeni parola en az 6 karakter olmalidir.'}), 400

    username = session.get('username')
    user_id = session.get('user_id')

    # 1. DC01 (Active Directory) uzerinde sifreyi guncelle
    ad_updated = False
    try:
        server = Server(LDAP_HOST, port=LDAP_PORT, connect_timeout=5)
        admin_conn = Connection(
            server,
            user=f'Administrator@{LDAP_DOMAIN}',
            password=os.getenv('LDAP_ADMIN_PASSWORD', 'aysima123'),
            auto_bind=True,
            receive_timeout=5
        )
        if admin_conn.bound:
            safe_u = escape_filter_chars(username)
            admin_conn.search(
                search_base=LDAP_BASE_DN,
                search_filter=f'(|(sAMAccountName={safe_u})(cn={safe_u}))',
                search_scope=SUBTREE,
                attributes=['entryDN']
            )
            if admin_conn.entries:
                user_dn = admin_conn.entries[0].entry_dn
                unicode_pass = ('\"' + new_password + '\"').encode('utf-16-le')
                admin_conn.modify(user_dn, {'unicodePwd': [(MODIFY_REPLACE, [unicode_pass])]})
                ad_updated = admin_conn.result.get('description') == 'success'
                print(f'AD Sifre Degisikligi ({username}): {admin_conn.result.get("description")}')
    except Exception as ex:
        print(f'AD sifre degistirme hatasi: {ex}')

    # 2. PostgreSQL veritabaninda guncelle
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            'UPDATE users SET password_hash = %s WHERE id = %s',
            (generate_password_hash(new_password), user_id)
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()

    msg = 'Parolaniz basariyla guncellendi!'
    if ad_updated:
        msg += ' Windows oturum sifreniz (Active Directory) ile senkronize edildi.'

    return jsonify({'success': True, 'message': msg}), 200
