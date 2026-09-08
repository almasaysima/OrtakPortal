from flask import (
    Blueprint,
    jsonify,
    request,
)

from backend.common.responses import api_error

from backend.common.request_utils import get_json_body

from itsdangerous import (
    BadSignature,
    SignatureExpired,
)

from backend.services.password_reset_service import (
    create_password_reset_token,
    find_user_by_email,
    load_password_reset_token,
    send_reset_email,
    update_password,
)


password_reset_bp = Blueprint(
    "password_reset",
    __name__,
    url_prefix="/api/password-reset",
)


@password_reset_bp.route(
    "/request",
    methods=["POST"],
)
def request_password_reset():
    data = get_json_body()

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip()

    if not email:
        return jsonify({
            "success": False,
            "error": "E-posta adresi zorunludur.",
        }), 400

    user = find_user_by_email(
        email
    )

    # Hesap var/yok bilgisini dışarı sızdırmamak için
    # aynı mesajı döndürüyoruz.
    if not user:
        return jsonify({
            "success": True,
            "message": (
                "Eğer bu e-posta adresi sistemde kayıtlıysa "
                "şifre sıfırlama bağlantısı gönderilecektir."
            ),
        }), 200

    token = create_password_reset_token(
        user[0]
    )

    reset_link = (
        request.host_url.rstrip("/")
        + f"/reset-password/{token}"
    )

    try:
        send_reset_email(
            user[1],
            reset_link,
        )

    except Exception as error:
        return jsonify({
            "success": False,
            "error": "Şifre sıfırlama maili gönderilemedi.",
            "detail": str(error),
        }), 500

    return jsonify({
        "success": True,
        "message": (
            "Eğer bu e-posta adresi sistemde kayıtlıysa "
            "şifre sıfırlama bağlantısı gönderilecektir."
        ),
    }), 200


@password_reset_bp.route(
    "/validate/<token>",
    methods=["GET"],
)
def validate_password_reset_token(
    token
):
    try:
        load_password_reset_token(
            token
        )

    except SignatureExpired:
        return jsonify({
            "success": False,
            "error": "Şifre sıfırlama bağlantısının süresi dolmuş.",
        }), 400

    except BadSignature:
        return jsonify({
            "success": False,
            "error": "Geçersiz şifre sıfırlama bağlantısı.",
        }), 400

    return jsonify({
        "success": True,
    }), 200


@password_reset_bp.route(
    "/reset/<token>",
    methods=["POST"],
)
def reset_password(
    token
):
    try:
        user_id = load_password_reset_token(
            token
        )

    except SignatureExpired:
        return jsonify({
            "success": False,
            "error": "Şifre sıfırlama bağlantısının süresi dolmuş.",
        }), 400

    except BadSignature:
        return jsonify({
            "success": False,
            "error": "Geçersiz şifre sıfırlama bağlantısı.",
        }), 400

    data = get_json_body()

    password = str(
        data.get(
            "password",
            ""
        )
    )

    confirm_password = str(
        data.get(
            "confirm_password",
            ""
        )
    )

    if len(password) < 6:
        return jsonify({
            "success": False,
            "error": "Şifre en az 6 karakter olmalıdır.",
        }), 400

    if password != confirm_password:
        return jsonify({
            "success": False,
            "error": "Girdiğiniz şifreler aynı değil.",
        }), 400

    update_password(
        user_id,
        password,
    )

    return jsonify({
        "success": True,
        "message": "Şifreniz başarıyla güncellendi.",
    }), 200
