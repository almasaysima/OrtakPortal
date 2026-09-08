# Flask içerisinden Blueprint yapısını import ediyoruz.
# Blueprint, büyük Flask uygulamasındaki route'ları
# farklı dosyalara ayırmamızı sağlar.
from flask import Blueprint


# Health ile ilgili endpoint'leri ayrı bir Blueprint altında topluyoruz.
# url_prefix="/api" olduğu için bu dosyadaki endpoint'ler
# /api ile başlayacak.
health_bp = Blueprint(
    "health",
    __name__,
    url_prefix="/api"
)


# Uygulamanın ayakta olup olmadığını kontrol etmek için
# kullanılacak health check endpoint'i.
#
# HTTP GET /api/health
# isteği geldiğinde bu fonksiyon çalışır.
@health_bp.route(
    "/health",
    methods=["GET"]
)
def health_check():

    # Backend servisinin durumunu JSON olarak döndürüyoruz.
    # Daha sonra Kubernetes bu endpoint'i kullanarak
    # servisin çalışıp çalışmadığını kontrol edebilir.
    return {
        "status": "ok",
        "service": "company-portal-backend"
    }