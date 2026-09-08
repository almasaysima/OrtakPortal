from flask import Flask

from backend.logging_config import configure_logging

from backend.config import (
    FLASK_DEBUG,
    FLASK_SECRET_KEY,
)

from backend.routes.announcements import (
    announcement_bp,
)
from backend.routes.auth import auth_bp
from backend.routes.departments import (
    department_bp,
)
from backend.routes.documents import (
    document_bp,
)
from backend.routes.employees import (
    employee_bp,
)
from backend.routes.events import event_bp
from backend.routes.health import health_bp
from backend.routes.leaves import leave_bp
from backend.routes.password_reset import (
    password_reset_bp,
)
from backend.routes.users import user_bp

from backend.services.startup_service import (
    ensure_initial_admin,
    ensure_minio_bucket,
)


def create_app():
    configure_logging()
    app = Flask(__name__)

    app.secret_key = FLASK_SECRET_KEY

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=28800,
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    )

    app.register_blueprint(
        health_bp
    )

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        department_bp
    )

    app.register_blueprint(
        employee_bp
    )

    app.register_blueprint(
        leave_bp
    )

    app.register_blueprint(
        announcement_bp
    )

    app.register_blueprint(
        event_bp
    )

    app.register_blueprint(
        user_bp
    )

    app.register_blueprint(
        document_bp
    )

    app.register_blueprint(
        password_reset_bp
    )

    # Gunicorn `app:app` ile import ettiğinde __main__ bloğu çalışmaz.
    # Bu nedenle ilk kurulum hazırlıkları app factory içinde yapılır.
    # Fonksiyonlar idempotent olduğu için birden fazla Gunicorn worker
    # tarafından çağrılsa da mevcut kayıtları tekrar oluşturmaz.
    ensure_minio_bucket()
    ensure_initial_admin()

    return app


app = create_app()


if __name__ == "__main__":
    print(
        "Company Portal backend başlatılıyor..."
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=FLASK_DEBUG,
    )
