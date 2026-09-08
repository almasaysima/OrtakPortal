import io

from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    send_file,
)

from backend.common.authz import (
    can_manage_content,
)

from backend.services.document_service import (
    list_documents,
    upload_document,
    get_document,
    read_document_bytes,
    delete_document,
)


document_bp = Blueprint(
    "documents_api",
    __name__,
    url_prefix="/api/documents",
)


# =========================================================
# DOSYALARI GETİR
# =========================================================

@document_bp.route(
    "",
    methods=["GET"],
)
def get_documents():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    return jsonify(
        list_documents()
    ), 200


# =========================================================
# DOSYA YÜKLE
# =========================================================

@document_bp.route(
    "",
    methods=["POST"],
)
def upload_document_api():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Dosya yükleme yetkiniz yok.",
        }), 403

    file = request.files.get(
        "file"
    )

    category = str(
        request.form.get(
            "category",
            "Genel",
        )
    ).strip() or "Genel"

    result = upload_document(
        file=file,
        category=category,
        uploaded_by=session["user_id"],
    )

    if not result["success"]:
        return jsonify(result), 400

    return jsonify(result), 201


# =========================================================
# DOSYA İNDİR
# =========================================================

@document_bp.route(
    "/<int:document_id>/download",
    methods=["GET"],
)
def download_document_api(
    document_id
):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    document = get_document(
        document_id
    )

    if not document:
        return jsonify({
            "success": False,
            "error": "Dosya bulunamadı.",
        }), 404

    file_bytes = read_document_bytes(
        document
    )

    if file_bytes is None:
        return jsonify({
            "success": False,
            "error": (
                "Dosya MinIO üzerinde bulunamadı."
            ),
        }), 404

    return send_file(
        io.BytesIO(file_bytes),
        as_attachment=True,
        download_name=document["file_name"],
    )


# =========================================================
# DOSYA SİL
# =========================================================

@document_bp.route(
    "/<int:document_id>",
    methods=["DELETE"],
)
def delete_document_api(
    document_id
):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor.",
        }), 401

    if not can_manage_content():
        return jsonify({
            "success": False,
            "error": "Dosya silme yetkiniz yok.",
        }), 403

    result = delete_document(
        document_id
    )

    if not result["success"]:
        return jsonify(result), 404

    return jsonify(result), 200
