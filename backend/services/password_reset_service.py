import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

from backend.config import (
    FLASK_SECRET_KEY,
    MAIL_HOST,
    MAIL_PORT,
    MAIL_USERNAME,
    MAIL_PASSWORD,
)
from backend.database.connection import get_db_connection


serializer = URLSafeTimedSerializer(
    FLASK_SECRET_KEY
)


def find_user_by_email(email):
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                email
            FROM users
            WHERE email = %s
            LIMIT 1
            """,
            (
                email,
            ),
        )

        user = cur.fetchone()
        cur.close()

        return user

    finally:
        conn.close()


def create_password_reset_token(user_id):
    return serializer.dumps(
        user_id,
        salt="password-reset",
    )


def load_password_reset_token(
    token,
    max_age=900,
):
    return serializer.loads(
        token,
        salt="password-reset",
        max_age=max_age,
    )


def send_reset_email(
    receiver_email,
    reset_link,
):
    if not MAIL_PASSWORD:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD environment variable tanımlı değil."
        )

    message = MIMEMultipart()

    message["From"] = MAIL_USERNAME
    message["To"] = receiver_email
    message["Subject"] = (
        "Company Portal - Şifre Sıfırlama"
    )

    body = f"""Merhaba,

Company Portal hesabınız için şifre sıfırlama talebi oluşturuldu.

Yeni şifrenizi belirlemek için aşağıdaki bağlantıyı kullanın:

{reset_link}

Bu bağlantı 15 dakika boyunca geçerlidir.

Eğer bu işlemi siz yapmadıysanız bu e-postayı dikkate almayabilirsiniz.

Company Portal
"""

    message.attach(
        MIMEText(
            body,
            "plain",
            "utf-8",
        )
    )

    with smtplib.SMTP(
        MAIL_HOST,
        MAIL_PORT,
        timeout=20,
    ) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(
            MAIL_USERNAME,
            MAIL_PASSWORD,
        )

        server.sendmail(
            MAIL_USERNAME,
            receiver_email,
            message.as_string(),
        )


def update_password(
    user_id,
    password,
):
    password_hash = generate_password_hash(
        password
    )

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET
                password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                password_hash,
                user_id,
            ),
        )

        conn.commit()
        cur.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
