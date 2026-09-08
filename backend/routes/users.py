from flask import (
    Blueprint,
    jsonify,
    request,
    session,
)

from backend.common.responses import api_error

from backend.common.request_utils import get_json_body

from backend.common.authz import (
    login_required,
    roles_required,
)

from backend.services.user_service import (
    list_users,
    create_user,
    update_user,
    delete_user,
)


user_bp = Blueprint(
    "users_api",
    __name__,
    url_prefix="/api/users",
)


def _require_user_management():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if session.get("role") not in (
        "admin",
        "hr_admin",
    ):
        return jsonify({
            "success": False,
            "error": "Kullanıcı yönetimi yetkiniz yok.",
        }), 403

    return None


@user_bp.route(
    "",
    methods=["GET"],
)
def get_users():
    error = _require_user_management()

    if error:
        return error

    return jsonify(
        list_users()
    ), 200


@user_bp.route(
    "",
    methods=["POST"],
)
def add_user_api():
    error = _require_user_management()

    if error:
        return error

    data = get_json_body()

    result = create_user(
        data=data,
        creator_role=session.get("role"),
    )

    if not result["success"]:
        return jsonify(result), 400

    return jsonify(result), 201


@user_bp.route(
    "/<int:user_id>",
    methods=["PUT"],
)
def edit_user_api(user_id):
    error = _require_user_management()

    if error:
        return error

    data = get_json_body()

    result = update_user(
        user_id=user_id,
        data=data,
        editor_role=session.get("role"),
    )

    if not result["success"]:
        return jsonify(result), 400

    return jsonify(result), 200


@user_bp.route(
    "/<int:user_id>",
    methods=["DELETE"],
)
def delete_user_api(user_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "error": "Kullanıcı silme yetkiniz yok.",
        }), 403

    result = delete_user(
        user_id=user_id,
        current_user_id=session["user_id"],
    )

    if not result["success"]:
        return jsonify(result), 400

    return jsonify(result), 200
