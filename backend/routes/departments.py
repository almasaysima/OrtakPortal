from flask import (
    Blueprint,
    jsonify,
    session,
)

from backend.common.responses import api_error

from backend.common.authz import (
    login_required,
)

from backend.services.department_service import (
    get_all_departments,
)


department_bp = Blueprint(
    "departments",
    __name__,
    url_prefix="/api/departments",
)


@department_bp.route(
    "",
    methods=["GET"],
)
def get_departments():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    departments = get_all_departments()

    result = [
        {
            "id": department[0],
            "name": department[1],
            "parent_id": department[2],
        }
        for department in departments
    ]

    return jsonify(result), 200
