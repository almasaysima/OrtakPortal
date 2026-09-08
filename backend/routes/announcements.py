from flask import (
    Blueprint,
    jsonify,
    session,
)

from backend.common.request_utils import get_json_body

from backend.common.authz import (
    can_manage_content,
    get_content_department,
    can_manage_department,
)

from backend.services.announcement_service import (
    get_announcements,
    create_announcement,
    update_announcement,
    delete_announcement,
)

from backend.database.connection import (
    get_db_connection,
)


announcement_bp = Blueprint(
    "announcements",
    __name__,
    url_prefix="/api/announcements",
)


def department_exists(department):
    if department == "Genel":
        return True

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1
            FROM departments
            WHERE name = %s
            LIMIT 1
            """,
            (department,),
        )

        exists = cur.fetchone() is not None
        cur.close()

        return exists

    finally:
        conn.close()


def get_announcement_department(announcement_id):
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT department
            FROM announcements
            WHERE id = %s
            """,
            (announcement_id,),
        )

        row = cur.fetchone()
        cur.close()

        if not row:
            return None

        return row[0]

    finally:
        conn.close()


# =========================================================
# DUYURULARI GETİR
# =========================================================

@announcement_bp.route("", methods=["GET"])
def list_announcements():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    role = session.get("role")

    department = session.get(
        "department",
        "Genel",
    )

    announcements = get_announcements(
        role=role,
        department=department,
    )

    return jsonify(announcements), 200


# =========================================================
# DUYURU OLUŞTUR
# =========================================================

@announcement_bp.route("", methods=["POST"])
def add_announcement_api():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Duyuru oluşturma yetkiniz yok.",
        }), 403

    data = get_json_body()

    title = str(
        data.get("title", "")
    ).strip()

    content = str(
        data.get("content", "")
    ).strip()

    requested_department = str(
        data.get("department", "")
    ).strip()

    if not title or not content:
        return jsonify({
            "success": False,
            "error": "Başlık ve içerik zorunludur.",
        }), 400

    department = get_content_department(
        requested_department
    )

    if not department:
        return jsonify({
            "success": False,
            "error": "Departman bilgisi belirlenemedi.",
        }), 403

    if not department_exists(department):
        return jsonify({
            "success": False,
            "error": "Geçersiz departman seçimi.",
        }), 400

    result = create_announcement(
        title=title,
        content=content,
        department=department,
        created_by=session["user_id"],
    )

    return jsonify({
        "success": True,
        "message": "Duyuru başarıyla oluşturuldu.",
        "announcement_id": result["id"],
    }), 201


# =========================================================
# DUYURU GÜNCELLE
# =========================================================

@announcement_bp.route(
    "/<int:announcement_id>",
    methods=["PUT"],
)
def edit_announcement_api(announcement_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Duyuru düzenleme yetkiniz yok.",
        }), 403

    current_department = (
        get_announcement_department(
            announcement_id
        )
    )

    if current_department is None:
        return jsonify({
            "success": False,
            "error": "Duyuru bulunamadı.",
        }), 404

    if not can_manage_department(
        current_department
    ):
        return jsonify({
            "success": False,
            "error": "Bu duyuruyu düzenleme yetkiniz yok.",
        }), 403

    data = get_json_body()

    title = str(
        data.get("title", "")
    ).strip()

    content = str(
        data.get("content", "")
    ).strip()

    requested_department = str(
        data.get("department", "")
    ).strip()

    if not title or not content:
        return jsonify({
            "success": False,
            "error": "Başlık ve içerik zorunludur.",
        }), 400

    department = get_content_department(
        requested_department
    )

    if not department:
        return jsonify({
            "success": False,
            "error": "Departman bilgisi belirlenemedi.",
        }), 403

    if not department_exists(department):
        return jsonify({
            "success": False,
            "error": "Geçersiz departman seçimi.",
        }), 400

    result = update_announcement(
        announcement_id=announcement_id,
        title=title,
        content=content,
        department=department,
    )

    if not result["success"]:
        return jsonify(result), 404

    return jsonify({
        "success": True,
        "message": "Duyuru başarıyla güncellendi.",
        "announcement_id": result["id"],
    }), 200


# =========================================================
# DUYURU SİL
# =========================================================

@announcement_bp.route(
    "/<int:announcement_id>",
    methods=["DELETE"],
)
def remove_announcement_api(announcement_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Duyuru silme yetkiniz yok.",
        }), 403

    current_department = (
        get_announcement_department(
            announcement_id
        )
    )

    if current_department is None:
        return jsonify({
            "success": False,
            "error": "Duyuru bulunamadı.",
        }), 404

    if not can_manage_department(
        current_department
    ):
        return jsonify({
            "success": False,
            "error": "Bu duyuruyu silme yetkiniz yok.",
        }), 403

    result = delete_announcement(
        announcement_id
    )

    if not result["success"]:
        return jsonify(result), 404

    return jsonify({
        "success": True,
        "message": "Duyuru başarıyla silindi.",
        "announcement_id": result["id"],
    }), 200
