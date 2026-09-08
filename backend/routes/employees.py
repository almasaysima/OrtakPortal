
from backend.common.responses import api_error
# Flask'ın Blueprint yapısını kullanıyoruz.
# Çalışan endpoint'lerini ayrı bir dosyada tutuyoruz.
from flask import Blueprint, request, jsonify, session

from backend.common.authz import (
    login_required,
)

# Çalışan arama işlemini service katmanına bırakıyoruz.
from backend.services.employee_service import search_employees


# Çalışanlarla ilgili endpoint'leri
# /api/employees altında topluyoruz.
employee_bp = Blueprint(
    "employees",
    __name__,
    url_prefix="/api/employees"
)


@employee_bp.route(
    "/search",
    methods=["GET"]
)
def search_employee_endpoint():
    """
    Çalışan arama endpoint'i.

    Örnek:
    GET /api/employees/search?q=ay
    """

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Oturum açmanız gerekiyor."
        }), 401

    # URL üzerinden gelen "q" parametresini alıyoruz.
    #
    # Örneğin:
    # /api/employees/search?q=ay
    #
    # burada search_text = "ay" olur.
    search_text = request.args.get(
        "q",
        ""
    )

    # Asıl arama işlemini service katmanına gönderiyoruz.
    # Route burada SQL sorgusu çalıştırmıyor.
    employees = search_employees(
        search_text
    )

    # Service katmanından gelen tuple listesini
    # JSON formatına dönüştürüyoruz.
    result = []

    for employee in employees:

        # Çalışan bilgilerini frontend'in
        # kolay kullanabileceği bir JSON yapısına çeviriyoruz.
        result.append({

            "id": employee[0],

            "first_name": employee[1],

            "last_name": employee[2],

            "email": employee[3],

            "department": employee[4],

            "manager_id": employee[5],

            # Yöneticisi varsa yönetici bilgilerini
            # ayrı bir nesne olarak döndürüyoruz.
            #
            # Yöneticisi yoksa None döndürüyoruz.
            "manager": {
                "first_name": employee[6],
                "last_name": employee[7]
            } if employee[6] or employee[7] else None
        })

    # JSON formatındaki sonuçları API istemcisine
    # geri döndürüyoruz.
    return jsonify(result)