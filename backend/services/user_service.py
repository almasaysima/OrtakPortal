from backend.database.connection import get_db_connection

from werkzeug.security import generate_password_hash


ALLOWED_ROLES = {
    "employee",
    "it_admin",
    "finance_admin",
    "hr_admin",
    "admin",
}

ALLOWED_DEPARTMENTS = {
    "Bilgi Teknolojileri",
    "Finans",
    "İnsan Kaynakları",
}


def list_users():
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                u.id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                COALESCE(d.name, u.department) AS department,
                u.role,
                u.status,
                u.manager_id,
                CONCAT_WS(' ', m.first_name, m.last_name) AS manager_name
            FROM users u
            LEFT JOIN departments d
                ON u.department_id = d.id
            LEFT JOIN users m
                ON u.manager_id = m.id
            ORDER BY
                u.first_name,
                u.last_name,
                u.username
        """)

        rows = cur.fetchall()
        cur.close()

        return [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "first_name": row[3],
                "last_name": row[4],
                "department": row[5],
                "role": str(row[6]),
                "status": str(row[7]),
                "manager_id": row[8],
                "manager_name": row[9] or None,
            }
            for row in rows
        ]

    finally:
        conn.close()


def _get_department(cur, department):
    cur.execute("""
        SELECT id
        FROM departments
        WHERE name = %s
        LIMIT 1
    """, (
        department,
    ))

    row = cur.fetchone()

    return row[0] if row else None


def create_user(data, creator_role):
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    first_name = str(data.get("first_name", "")).strip()
    last_name = str(data.get("last_name", "")).strip()
    department = str(data.get("department", "")).strip()
    role = str(data.get("role", "employee")).strip().lower()
    password = str(data.get("password", ""))
    manager_id = data.get("manager_id")

    if not all([
        username,
        email,
        first_name,
        last_name,
        department,
        password,
    ]):
        return {
            "success": False,
            "error": "Tüm zorunlu alanları doldurun.",
        }

    if len(password) < 6:
        return {
            "success": False,
            "error": "Şifre en az 6 karakter olmalıdır.",
        }

    if department not in ALLOWED_DEPARTMENTS:
        return {
            "success": False,
            "error": "Geçersiz departman seçimi.",
        }

    allowed_roles = {
        "employee",
        "it_admin",
        "finance_admin",
        "hr_admin",
    }

    if creator_role == "admin":
        allowed_roles.add("admin")

    if role not in allowed_roles:
        return {
            "success": False,
            "error": "Bu rolü oluşturma yetkiniz yok.",
        }

    if role == "it_admin" and department != "Bilgi Teknolojileri":
        return {
            "success": False,
            "error": "IT Yöneticisi yalnızca IT departmanında olabilir.",
        }

    if role == "finance_admin" and department != "Finans":
        return {
            "success": False,
            "error": "Finans Yöneticisi yalnızca Finans departmanında olabilir.",
        }

    if role == "hr_admin" and department != "İnsan Kaynakları":
        return {
            "success": False,
            "error": "İK Admin yalnızca İnsan Kaynakları departmanında olabilir.",
        }

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM users
            WHERE username = %s
               OR email = %s
            LIMIT 1
        """, (
            username,
            email,
        ))

        if cur.fetchone():
            cur.close()

            return {
                "success": False,
                "error": "Kullanıcı adı veya e-posta zaten kullanılıyor.",
            }

        department_id = _get_department(
            cur,
            department,
        )

        if not department_id:
            cur.close()

            return {
                "success": False,
                "error": "Departman bulunamadı.",
            }

        if manager_id in (
            "",
            None,
        ):
            manager_id = None
        else:
            try:
                manager_id = int(manager_id)
            except (TypeError, ValueError):
                cur.close()

                return {
                    "success": False,
                    "error": "Geçersiz yönetici seçimi.",
                }

        password_hash = generate_password_hash(
            password
        )

        cur.execute("""
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                first_name,
                last_name,
                department,
                department_id,
                manager_id,
                role
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
        """, (
            username,
            email,
            password_hash,
            first_name,
            last_name,
            department,
            department_id,
            manager_id,
            role,
        ))

        user_id = cur.fetchone()[0]

        conn.commit()
        cur.close()

        return {
            "success": True,
            "id": user_id,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def update_user(user_id, data, editor_role):
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    first_name = str(data.get("first_name", "")).strip()
    last_name = str(data.get("last_name", "")).strip()
    department = str(data.get("department", "")).strip()
    role = str(data.get("role", "employee")).strip().lower()
    new_password = str(data.get("new_password", ""))
    manager_id = data.get("manager_id")

    if not all([
        username,
        email,
        first_name,
        last_name,
        department,
    ]):
        return {
            "success": False,
            "error": "Zorunlu alanlar boş bırakılamaz.",
        }

    if department not in ALLOWED_DEPARTMENTS:
        return {
            "success": False,
            "error": "Geçersiz departman seçimi.",
        }

    allowed_roles = {
        "employee",
        "it_admin",
        "finance_admin",
        "hr_admin",
    }

    if editor_role == "admin":
        allowed_roles.add("admin")

    if role not in allowed_roles:
        return {
            "success": False,
            "error": "Bu rolü atama yetkiniz yok.",
        }

    if role == "it_admin" and department != "Bilgi Teknolojileri":
        return {
            "success": False,
            "error": "IT Yöneticisi yalnızca IT departmanında olabilir.",
        }

    if role == "finance_admin" and department != "Finans":
        return {
            "success": False,
            "error": "Finans Yöneticisi yalnızca Finans departmanında olabilir.",
        }

    if role == "hr_admin" and department != "İnsan Kaynakları":
        return {
            "success": False,
            "error": "İK Admin yalnızca İnsan Kaynakları departmanında olabilir.",
        }

    if new_password and len(new_password) < 6:
        return {
            "success": False,
            "error": "Yeni şifre en az 6 karakter olmalıdır.",
        }

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT role
            FROM users
            WHERE id = %s
        """, (
            user_id,
        ))

        current = cur.fetchone()

        if not current:
            cur.close()

            return {
                "success": False,
                "error": "Kullanıcı bulunamadı.",
            }

        if (
            editor_role == "hr_admin"
            and str(current[0]) == "admin"
        ):
            cur.close()

            return {
                "success": False,
                "error": "Genel admin hesabını düzenleyemezsiniz.",
            }

        cur.execute("""
            SELECT id
            FROM users
            WHERE
                (username = %s OR email = %s)
                AND id <> %s
            LIMIT 1
        """, (
            username,
            email,
            user_id,
        ))

        if cur.fetchone():
            cur.close()

            return {
                "success": False,
                "error": "Kullanıcı adı veya e-posta başka bir kullanıcı tarafından kullanılıyor.",
            }

        department_id = _get_department(
            cur,
            department,
        )

        if not department_id:
            cur.close()

            return {
                "success": False,
                "error": "Departman bulunamadı.",
            }

        if manager_id in (
            "",
            None,
        ):
            manager_id = None
        else:
            try:
                manager_id = int(manager_id)
            except (TypeError, ValueError):
                cur.close()

                return {
                    "success": False,
                    "error": "Geçersiz yönetici seçimi.",
                }

        if manager_id == user_id:
            cur.close()

            return {
                "success": False,
                "error": "Kullanıcı kendi yöneticisi olamaz.",
            }

        if new_password:
            password_hash = generate_password_hash(
                new_password
            )

            cur.execute("""
                UPDATE users
                SET
                    username = %s,
                    email = %s,
                    first_name = %s,
                    last_name = %s,
                    department = %s,
                    department_id = %s,
                    manager_id = %s,
                    role = %s,
                    password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                username,
                email,
                first_name,
                last_name,
                department,
                department_id,
                manager_id,
                role,
                password_hash,
                user_id,
            ))

        else:
            cur.execute("""
                UPDATE users
                SET
                    username = %s,
                    email = %s,
                    first_name = %s,
                    last_name = %s,
                    department = %s,
                    department_id = %s,
                    manager_id = %s,
                    role = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                username,
                email,
                first_name,
                last_name,
                department,
                department_id,
                manager_id,
                role,
                user_id,
            ))

        conn.commit()
        cur.close()

        return {
            "success": True,
            "id": user_id,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def delete_user(user_id, current_user_id):
    if user_id == current_user_id:
        return {
            "success": False,
            "error": "Kendi hesabınızı silemezsiniz.",
        }

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM users
            WHERE id = %s
            RETURNING id
        """, (
            user_id,
        ))

        deleted = cur.fetchone()

        if not deleted:
            conn.rollback()
            cur.close()

            return {
                "success": False,
                "error": "Kullanıcı bulunamadı.",
            }

        conn.commit()
        cur.close()

        return {
            "success": True,
            "id": deleted[0],
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
