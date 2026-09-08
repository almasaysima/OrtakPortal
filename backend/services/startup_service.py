import time

from minio import Minio
from minio.error import S3Error
from werkzeug.security import generate_password_hash

from backend.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    INITIAL_ADMIN_USERNAME,
    INITIAL_ADMIN_PASSWORD,
    INITIAL_ADMIN_EMAIL,
)
from backend.database.connection import get_db_connection


def ensure_minio_bucket(
    retries=15,
    delay_seconds=2,
):
    """
    MinIO bucket'ının hazır olduğundan emin olur.

    Fonksiyon idempotenttir:
    bucket zaten varsa hiçbir değişiklik yapmaz.
    """

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    last_error = None

    for _ in range(retries):
        try:
            if client.bucket_exists(
                MINIO_BUCKET
            ):
                return

            try:
                client.make_bucket(
                    MINIO_BUCKET
                )
            except S3Error as error:
                # Birden fazla Gunicorn worker aynı anda ilk açılışı
                # yaparsa başka worker bucket'ı arada oluşturmuş olabilir.
                if error.code not in (
                    "BucketAlreadyOwnedByYou",
                    "BucketAlreadyExists",
                ):
                    raise

            return

        except Exception as error:
            last_error = error
            time.sleep(delay_seconds)

    raise RuntimeError(
        "MinIO bucket hazırlanamadı."
    ) from last_error


def ensure_initial_admin():
    """
    İlk genel admin hesabını güvenli ve tekrar çalıştırılabilir
    şekilde oluşturur.

    Birden fazla Gunicorn worker aynı anda başlasa bile
    ON CONFLICT sayesinde duplicate admin oluşmaz.
    """

    password_hash = generate_password_hash(
        INITIAL_ADMIN_PASSWORD
    )

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                first_name,
                last_name,
                department,
                department_id,
                role
            )
            SELECT
                %s,
                %s,
                %s,
                'System',
                'Admin',
                d.name,
                d.id,
                'admin'
            FROM departments d
            WHERE d.name = 'Bilgi Teknolojileri'
            LIMIT 1
            ON CONFLICT DO NOTHING
            """,
            (
                INITIAL_ADMIN_USERNAME,
                INITIAL_ADMIN_EMAIL,
                password_hash,
            ),
        )

        conn.commit()
        cur.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
