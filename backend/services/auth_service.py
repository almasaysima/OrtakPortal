# =========================================================
# AUTH SERVICE (Evrensel Search-then-Bind LDAP + Yerel DB)
# =========================================================

import secrets
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.utils.conv import escape_filter_chars
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.connection import get_db_connection
from backend.config import (
    LDAP_ENABLED,
    LDAP_HOST,
    LDAP_PORT,
    LDAP_DOMAIN,
    LDAP_BASE_DN,
)

GROUP_ROLE_MAP = {
    "OrtakPortal-GenelAdmin": {
        "role": "admin",
        "department": "Genel",
    },
    "OrtakPortal-IT-Yonetici": {
        "role": "it_admin",
        "department": "Bilgi Teknolojileri",
    },
    "OrtakPortal-IT-Calisan": {
        "role": "employee",
        "department": "Bilgi Teknolojileri",
    },
    "OrtakPortal-Finans-Yonetici": {
        "role": "finance_admin",
        "department": "Finans",
    },
    "OrtakPortal-Finans-Calisan": {
        "role": "employee",
        "department": "Finans",
    },
    "OrtakPortal-IK-Yonetici": {
        "role": "hr_admin",
        "department": "İnsan Kaynakları",
    },
    "OrtakPortal-IK-Calisan": {
        "role": "employee",
        "department": "İnsan Kaynakları",
    },
}

def get_first_attribute(attributes, key, default=""):
    val = attributes.get(key, default)
    if isinstance(val, list):
        return val[0] if val else default
    return val

def get_profile_from_groups(member_of):
    for item in member_of:
        item_str = str(item)
        for group_name, profile in GROUP_ROLE_MAP.items():
            if group_name.lower() in item_str.lower():
                return profile
    return None

def get_portal_user(username):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT u.id, u.username, u.password_hash, u.role, d.name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE LOWER(u.username) = LOWER(%s)
            LIMIT 1
            ''',
            (username,),
        )
        return cur.fetchone()
    finally:
        conn.close()

def authenticate_local_admin(username, password):
    user = get_portal_user(username)
    if not user:
        return None
    if not user or not check_password_hash(user[2], password):
        return None
    return {
        "id": user[0],
        "username": user[1],
        "role": str(user[3]),
        "department": user[4] if user[4] else "Genel",
    }

def sync_ad_user(ad_user):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        department_id = None
        if ad_user["department"] != "Genel":
            cur.execute(
                "SELECT id FROM departments WHERE name = %s LIMIT 1",
                (ad_user["department"],)
            )
            dept_row = cur.fetchone()
            if dept_row:
                department_id = dept_row[0]

        manager_id = None
        if ad_user["role"] == "employee" and department_id:
            cur.execute(
                "SELECT manager_id FROM departments WHERE id = %s",
                (department_id,)
            )
            mgr_row = cur.fetchone()
            if mgr_row and mgr_row[0]:
                manager_id = mgr_row[0]

        cur.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (ad_user["username"],)
        )
        existing = cur.fetchone()

        if existing:
            user_id = existing[0]
            cur.execute(
                '''
                UPDATE users
                SET email = %s, role = %s, department_id = COALESCE(%s, department_id),
                    manager_id = COALESCE(%s, manager_id)
                WHERE id = %s
                ''',
                (ad_user["email"], ad_user["role"], department_id, manager_id, user_id)
            )
        else:
            dummy_hash = generate_password_hash(secrets.token_hex(16))
            cur.execute(
                '''
                INSERT INTO users (username, email, password_hash, role, department_id, manager_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                ''',
                (ad_user["username"], ad_user["email"], dummy_hash, ad_user["role"], department_id, manager_id)
            )
            user_id = cur.fetchone()[0]

        conn.commit()
        return {
            "id": user_id,
            "username": ad_user["username"],
            "role": ad_user["role"],
            "department": ad_user["department"],
        }
    except Exception as ex:
        conn.rollback()
        print(f"sync_ad_user hatasi: {ex}")
        return None
    finally:
        conn.close()

def authenticate_ldap(username, password):
    if not LDAP_ENABLED:
        return None

    server = Server(LDAP_HOST, port=LDAP_PORT, connect_timeout=5)

    # 1. Admin / Servis Hesabi ile Baglanti
    admin_candidates = [
        ("cn=admin,dc=sirket,dc=local", "AdminPassword123!"),
        (f"admin@{LDAP_DOMAIN}", "AdminPassword123!"),
    ]
    admin_conn = None
    for adn, apw in admin_candidates:
        try:
            c = Connection(server, user=adn, password=apw, auto_bind=True, receive_timeout=5)
            if c.bound:
                admin_conn = c
                break
        except Exception:
            continue

    if not admin_conn:
        return None

    try:
        safe_username = escape_filter_chars(username)
        entry = None

        # 2. Kullaniciyi Ara (Once OpenLDAP cn/uid formatinda dene)
        try:
            admin_conn.search(
                search_base=LDAP_BASE_DN,
                search_filter=f"(|(cn={safe_username})(uid={safe_username}))",
                search_scope=SUBTREE,
                attributes=["cn", "givenName", "sn", "displayName", "mail", "memberOf"]
            )
            if admin_conn.entries:
                entry = admin_conn.entries[0]
        except Exception:
            entry = None

        # Eger bulunamadiysa Active Directory (sAMAccountName) ile ara
        if not entry:
            try:
                admin_conn.search(
                    search_base=LDAP_BASE_DN,
                    search_filter=f"(sAMAccountName={safe_username})",
                    search_scope=SUBTREE,
                    attributes=["sAMAccountName", "givenName", "sn", "displayName", "mail", "memberOf"]
                )
                if admin_conn.entries:
                    entry = admin_conn.entries[0]
            except Exception:
                entry = None

        if not entry:
            return None

        user_dn = entry.entry_dn

        # 3. Kullanicinin Parolasini Dogrula (User Bind)
        try:
            user_conn = Connection(server, user=user_dn, password=password, auto_bind=True, receive_timeout=5)
            if not user_conn.bound:
                return None
        except Exception:
            return None

        # 4. Grup Uyeligini Al
        attributes = entry.entry_attributes_as_dict
        member_of = attributes.get("memberOf", [])
        if not member_of:
            try:
                admin_conn.search(
                    search_base=LDAP_BASE_DN,
                    search_filter=f"(member={user_dn})",
                    search_scope=SUBTREE,
                    attributes=["cn"]
                )
                member_of = [f"cn={g.cn.value},ou=groups,{LDAP_BASE_DN}" for g in admin_conn.entries]
            except Exception:
                pass

        profile = get_profile_from_groups(member_of)
        if not profile:
            profile = {"role": "employee", "department": "Bilgi Teknolojileri"}

        first_name = str(get_first_attribute(attributes, "givenName", ""))
        last_name = str(get_first_attribute(attributes, "sn", ""))
        display_name = str(get_first_attribute(attributes, "displayName", username))
        mail = str(get_first_attribute(attributes, "mail", f"{username}@{LDAP_DOMAIN}"))

        return {
            "username": username,
            "first_name": first_name or display_name,
            "last_name": last_name,
            "display_name": display_name,
            "email": mail,
            "role": profile["role"],
            "department": profile["department"],
        }
    except Exception as ex:
        print(f"LDAP akis hatasi: {ex}")
        return None

def authenticate_user(username, password):
    if username.lower() == "admin":
        return authenticate_local_admin(username, password)

    if LDAP_ENABLED:
        ad_user = authenticate_ldap(username, password)
        if ad_user:
            return sync_ad_user(ad_user)

    return authenticate_local_admin(username, password)
