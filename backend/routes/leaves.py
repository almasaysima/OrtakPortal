# Flask'ın gerekli yapılarını import ediyoruz.
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
    roles_required,
)

# İzin service katmanındaki business logic fonksiyonlarını
# route katmanına aktarıyoruz.
from backend.services.leave_service import (
    create_leave_request,
    get_my_leave_requests,
    approve_leave_request,
    reject_leave_request,
    get_pending_leave_requests,
    get_all_leave_requests
)   

# Tarih doğrulaması için datetime kullanıyoruz.
from datetime import datetime


# İzin endpoint'lerini /api/leaves altında topluyoruz.
leave_bp = Blueprint(
    "leaves",
    __name__,
    url_prefix="/api/leaves"
)


# =========================================================
# İZİN OLUŞTUR
# =========================================================

@leave_bp.route(
    "",
    methods=["POST"]
)
def create_leave():
    """
    Yeni izin talebi oluşturur.

    Örnek:
    POST /api/leaves
    """

    # -------------------------------------------------
    # KULLANICI KONTROLÜ
    # -------------------------------------------------

    # Giriş yapmamış kullanıcı izin oluşturamaz.
    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor."
        }), 401

    user_id = session["user_id"]

    # -------------------------------------------------
    # REQUEST VERİSİNİ AL
    # -------------------------------------------------

    # JSON body içindeki verileri alıyoruz.
    #
    # Örnek:
    #
    # {
    #   "start_date": "2026-08-25",
    #   "end_date": "2026-08-27",
    #   "reason": "Yıllık izin"
    # }

    data = get_json_body()

    start_date = str(
        data.get("start_date", "")
    ).strip()

    end_date = str(
        data.get("end_date", "")
    ).strip()

    reason = str(
        data.get("reason", "")
    ).strip()

    # -------------------------------------------------
    # ZORUNLU ALAN KONTROLÜ
    # -------------------------------------------------

    if not start_date:

        return jsonify({
            "success": False,
            "error": "Başlangıç tarihi zorunludur."
        }), 400

    if not end_date:

        return jsonify({
            "success": False,
            "error": "Bitiş tarihi zorunludur."
        }), 400

    if not reason:

        return jsonify({
            "success": False,
            "error": "İzin açıklaması zorunludur."
        }), 400

    # -------------------------------------------------
    # TARİH KONTROLÜ
    # -------------------------------------------------

    try:

        start = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        end = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return jsonify({
            "success": False,
            "error": "Geçersiz tarih formatı."
        }), 400

    # Bitiş tarihi başlangıç tarihinden önce olamaz.
    if end < start:

        return jsonify({
            "success": False,
            "error": (
                "Bitiş tarihi başlangıç "
                "tarihinden önce olamaz."
            )
        }), 400

    # -------------------------------------------------
    # SERVICE KATMANINI ÇAĞIR
    # -------------------------------------------------

    # Veritabanı ve business logic işlemlerini
    # service katmanına bırakıyoruz.
    result = create_leave_request(
        user_id=user_id,
        start_date=start,
        end_date=end,
        reason=reason
    )

    # Service işlemi başarısız olduysa
    # hata mesajını API olarak döndürüyoruz.
    if not result["success"]:

        return jsonify(result), 400

    # İzin başarıyla oluşturuldu.
    return jsonify({
        "success": True,
        "message": (
            "İzin talebiniz başarıyla oluşturuldu."
        ),
        "leave_id": result["leave_id"],
        "manager_id": result["manager_id"],
        "approval_stage": result["approval_stage"]
    }), 201


# =========================================================
# KENDİ İZİNLERİNİ GETİR
# =========================================================

@leave_bp.route(
    "/my",
    methods=["GET"]
)
def get_my_leaves():
    """
    Giriş yapan çalışanın kendi izin taleplerini döndürür.

    GET /api/leaves/my
    """

    # Kullanıcı giriş yapmamışsa
    # izin kayıtlarını göremez.
    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor."
        }), 401

    # Kullanıcının ID'sini session'dan alıyoruz.
    # Böylece kullanıcı başka bir kişinin ID'sini
    # göndererek onun izinlerini göremez.
    user_id = session["user_id"]

    # Veritabanı işlemini service katmanına bırakıyoruz.
    requests = get_my_leave_requests(
        user_id
    )

    # Service'den gelen verileri
    # frontend'in kullanabileceği JSON yapısına çeviriyoruz.
    result = []

    for leave in requests:

        result.append({

            "id": leave[0],

            "start_date": leave[1].isoformat(),

            "end_date": leave[2].isoformat(),

            "reason": leave[3],

            "status": leave[4],

            "approval_stage": leave[5],

            "admin_note": leave[6],

            "created_at": (
                leave[7].isoformat()
                if leave[7]
                else None
            ),

            "attachment_name": leave[8],

            "manager_note": leave[9],

            "hr_note": leave[10],

            # Yöneticisi varsa bilgilerini
            # ayrı bir nesne olarak döndürüyoruz.
            "manager": {
                "first_name": leave[11],
                "last_name": leave[12]
            } if leave[11] or leave[12] else None
        })

    return jsonify(result)


# =========================================================
# İZİN ONAYLA
# =========================================================

@leave_bp.route(
    "/<int:request_id>/approve",
    methods=["POST"]
)
def approve_leave(request_id):
    """
    İzin talebini mevcut onay aşamasına göre onaylar.

    POST /api/leaves/<request_id>/approve
    """

    # Kullanıcı giriş yapmamışsa onay işlemi yapamaz.
    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor."
        }), 401

    # Giriş yapan kullanıcının ID'sini session'dan alıyoruz.
    reviewer_id = session["user_id"]

    # JSON body içinden onay notunu alıyoruz.
    data = get_json_body()

    note = str(
        data.get("note", "")
    ).strip()

    # Asıl yetki ve business logic kontrolünü
    # service katmanına bırakıyoruz.
    result = approve_leave_request(
        request_id=request_id,
        reviewer_id=reviewer_id,
        note=note
    )

    # Service işlemi reddettiyse hata döndürüyoruz.
    if not result["success"]:

        return jsonify(result), 403

    # İşlem başarılıysa sonucu JSON olarak döndürüyoruz.
    return jsonify(result), 200


# =========================================================
# İZİN REDDET
# =========================================================

@leave_bp.route(
    "/<int:request_id>/reject",
    methods=["POST"]
)
def reject_leave(request_id):
    """
    İzin talebini mevcut onay aşamasına göre reddeder.

    POST /api/leaves/<request_id>/reject
    """

    # Kullanıcı giriş yapmamışsa red işlemi yapamaz.
    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor."
        }), 401

    # Giriş yapan kullanıcının ID'sini session'dan alıyoruz.
    reviewer_id = session["user_id"]

    # JSON body içinden red notunu alıyoruz.
    data = get_json_body()

    note = str(
        data.get("note", "")
    ).strip()

    # Yetki kontrolü ve business logic
    # service katmanında gerçekleştiriliyor.
    result = reject_leave_request(
        request_id=request_id,
        reviewer_id=reviewer_id,
        note=note
    )

    # Yetkisiz veya geçersiz bir işlemse
    # uygun hata kodunu döndürüyoruz.
    if not result["success"]:

        return jsonify(result), 403

    # İşlem başarılıysa sonucu JSON olarak döndürüyoruz.
    return jsonify(result), 200

    # =========================================================
# BEKLEYEN İZİNLERİ GETİR
# =========================================================

@leave_bp.route(
    "/pending",
    methods=["GET"]
)
def get_pending_leaves():
    """
    Giriş yapan kullanıcının onaylayabileceği
    bekleyen izin taleplerini döndürür.

    GET /api/leaves/pending
    """

    # Kullanıcı giriş yapmamışsa
    # bekleyen izinleri göremez.
    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor."
        }), 401

    # Giriş yapan kullanıcının ID'sini
    # session üzerinden alıyoruz.
    reviewer_id = session["user_id"]

    # Asıl yetki ve veri erişimi kontrolünü
    # service katmanına bırakıyoruz.
    result = get_pending_leave_requests(
        reviewer_id
    )

    # Service bir hata döndürdüyse
    # uygun HTTP cevabını oluşturuyoruz.
    if not result["success"]:

        return jsonify(result), 403

    # Service'den gelen kayıtları
    # frontend'in kullanabileceği JSON formatına çeviriyoruz.
    requests = result["requests"]

    response = []

    for leave in requests:

        response.append({
            "id": leave[0],
            "user_id": leave[1],
            "first_name": leave[2],
            "last_name": leave[3],
            "department": leave[4],
            "start_date": leave[5].isoformat(),
            "end_date": leave[6].isoformat(),
            "reason": leave[7],
            "status": leave[8],
            "approval_stage": leave[9],
            "created_at": (
                leave[10].isoformat()
                if leave[10]
                else None
            )
        })

    return jsonify(response), 200

# =========================================================
# ADMIN / İK İÇİN TÜM İZİN TALEPLERİ
# =========================================================

@leave_bp.route(
    "/admin",
    methods=["GET"],
)
def get_admin_leaves():
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
            "error": "İzin yönetimi yetkiniz yok.",
        }), 403

    rows = get_all_leave_requests()

    result = []

    for leave in rows:
        result.append({
            "id": leave[0],
            "user_id": leave[1],
            "first_name": leave[2],
            "last_name": leave[3],
            "department": leave[4],
            "start_date": leave[5].isoformat(),
            "end_date": leave[6].isoformat(),
            "reason": leave[7],
            "status": leave[8],
            "approval_stage": leave[9],
            "admin_note": leave[10],
            "manager_note": leave[11],
            "hr_note": leave[12],
            "created_at": (
                leave[13].isoformat()
                if leave[13]
                else None
            ),
        })

    return jsonify(result), 200
