from datetime import datetime

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

from backend.services.event_service import (
    get_events,
    create_event,
    update_event,
    delete_event,
)

from backend.database.connection import (
    get_db_connection,
)


event_bp = Blueprint(
    "events",
    __name__,
    url_prefix="/api/events",
)


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

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


def get_event_department(event_id):
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT department
            FROM events
            WHERE id = %s
            """,
            (event_id,),
        )

        row = cur.fetchone()
        cur.close()

        if not row:
            return None

        return row[0]

    finally:
        conn.close()


# =========================================================
# ETKİNLİKLERİ GETİR
# =========================================================

@event_bp.route("", methods=["GET"])
def list_events():

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

    events = get_events(
        role=role,
        department=department,
    )

    return jsonify(events), 200


# =========================================================
# ETKİNLİK OLUŞTUR
# =========================================================

@event_bp.route("", methods=["POST"])
def add_event_api():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Etkinlik oluşturma yetkiniz yok.",
        }), 403

    data = get_json_body()

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    event_date = str(
        data.get("event_date", "")
    ).strip()

    location = str(
        data.get("location", "")
    ).strip()

    requested_department = str(
        data.get("department", "")
    ).strip()

    if (
        not title
        or not description
        or not event_date
    ):
        return jsonify({
            "success": False,
            "error": (
                "Başlık, açıklama ve "
                "etkinlik tarihi zorunludur."
            ),
        }), 400

    try:
        parsed_event_date = (
            datetime.fromisoformat(
                event_date
            )
        )

    except ValueError:
        return jsonify({
            "success": False,
            "error": "Geçersiz etkinlik tarihi.",
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

    result = create_event(
        title=title,
        description=description,
        event_date=parsed_event_date,
        location=location,
        department=department,
        created_by=session["user_id"],
    )

    return jsonify({
        "success": True,
        "message": "Etkinlik başarıyla oluşturuldu.",
        "event_id": result["id"],
    }), 201


# =========================================================
# ETKİNLİK GÜNCELLE
# =========================================================

@event_bp.route(
    "/<int:event_id>",
    methods=["PUT"],
)
def edit_event_api(event_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Etkinlik düzenleme yetkiniz yok.",
        }), 403

    current_department = (
        get_event_department(event_id)
    )

    if current_department is None:
        return jsonify({
            "success": False,
            "error": "Etkinlik bulunamadı.",
        }), 404

    if not can_manage_department(
        current_department
    ):
        return jsonify({
            "success": False,
            "error": "Bu etkinliği düzenleme yetkiniz yok.",
        }), 403

    data = get_json_body()

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    event_date = str(
        data.get("event_date", "")
    ).strip()

    location = str(
        data.get("location", "")
    ).strip()

    requested_department = str(
        data.get("department", "")
    ).strip()

    if (
        not title
        or not description
        or not event_date
    ):
        return jsonify({
            "success": False,
            "error": (
                "Başlık, açıklama ve "
                "etkinlik tarihi zorunludur."
            ),
        }), 400

    try:
        parsed_event_date = (
            datetime.fromisoformat(
                event_date
            )
        )

    except ValueError:
        return jsonify({
            "success": False,
            "error": "Geçersiz etkinlik tarihi.",
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

    result = update_event(
        event_id=event_id,
        title=title,
        description=description,
        event_date=parsed_event_date,
        location=location,
        department=department,
    )

    if not result["success"]:
        return jsonify(result), 404

    return jsonify({
        "success": True,
        "message": "Etkinlik başarıyla güncellendi.",
        "event_id": result["id"],
    }), 200


# =========================================================
# ETKİNLİK SİL
# =========================================================

@event_bp.route(
    "/<int:event_id>",
    methods=["DELETE"],
)
def remove_event_api(event_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Etkinlik silme yetkiniz yok.",
        }), 403

    current_department = (
        get_event_department(event_id)
    )

    if current_department is None:
        return jsonify({
            "success": False,
            "error": "Etkinlik bulunamadı.",
        }), 404

    if not can_manage_department(
        current_department
    ):
        return jsonify({
            "success": False,
            "error": "Bu etkinliği silme yetkiniz yok.",
        }), 403

    result = delete_event(event_id)

    if not result["success"]:
        return jsonify(result), 404

    return jsonify({
        "success": True,
        "message": "Etkinlik başarıyla silindi.",
        "event_id": result["id"],
    }), 200
