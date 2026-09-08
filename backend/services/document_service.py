import logging

import io
import uuid

from minio import Minio
from minio.error import S3Error

from werkzeug.utils import secure_filename

from backend.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
)
from backend.database.connection import get_db_connection


minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)



logger = logging.getLogger(__name__)

def list_documents():
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                d.id,
                d.file_name,
                d.category,
                d.uploaded_at,
                u.username
            FROM documents d
            LEFT JOIN users u
                ON d.uploaded_by = u.id
            ORDER BY d.uploaded_at DESC
        """)

        rows = cur.fetchall()
        cur.close()

        return [
            {
                "id": row[0],
                "file_name": row[1],
                "category": row[2],
                "uploaded_at": (
                    row[3].isoformat()
                    if row[3]
                    else None
                ),
                "uploaded_by": row[4],
            }
            for row in rows
        ]

    finally:
        conn.close()


def upload_document(file, category, uploaded_by):
    if not file or not file.filename:
        return {
            "success": False,
            "error": "Dosya seçmelisiniz.",
        }

    original_name = secure_filename(
        file.filename
    )

    if not original_name:
        return {
            "success": False,
            "error": "Geçerli bir dosya adı bulunamadı.",
        }

    file_data = file.read()

    max_size = 20 * 1024 * 1024

    if len(file_data) > max_size:
        return {
            "success": False,
            "error": "Dosya boyutu en fazla 20 MB olabilir.",
        }

    object_name = (
        f"{uuid.uuid4()}_{original_name}"
    )

    try:
        minio_client.put_object(
            MINIO_BUCKET,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=(
                file.content_type
                or "application/octet-stream"
            ),
        )

    except S3Error as error:
        logger.exception("MinIO yükleme hatası: %s", error)

        return {
            "success": False,
            "error": "Dosya MinIO'ya yüklenemedi.",
        }

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO documents
            (
                file_name,
                object_name,
                category,
                uploaded_by
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
        """, (
            original_name,
            object_name,
            category,
            uploaded_by,
        ))

        document_id = cur.fetchone()[0]

        conn.commit()
        cur.close()

        return {
            "success": True,
            "id": document_id,
        }

    except Exception:
        conn.rollback()

        try:
            minio_client.remove_object(
                MINIO_BUCKET,
                object_name,
            )
        except S3Error:
            pass

        raise

    finally:
        conn.close()


def get_document(document_id):
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                file_name,
                object_name
            FROM documents
            WHERE id = %s
        """, (
            document_id,
        ))

        row = cur.fetchone()
        cur.close()

        if not row:
            return None

        return {
            "file_name": row[0],
            "object_name": row[1],
        }

    finally:
        conn.close()


def read_document_bytes(document):
    try:
        response = minio_client.get_object(
            MINIO_BUCKET,
            document["object_name"],
        )

        file_bytes = response.read()

        response.close()
        response.release_conn()

        return file_bytes

    except S3Error:
        return None


def delete_document(document_id):
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT object_name
            FROM documents
            WHERE id = %s
        """, (
            document_id,
        ))

        row = cur.fetchone()

        if not row:
            cur.close()

            return {
                "success": False,
                "error": "Dosya bulunamadı.",
            }

        try:
            minio_client.remove_object(
                MINIO_BUCKET,
                row[0],
            )
        except S3Error as error:
            logger.warning("MinIO silme hatası: %s", error)

        cur.execute("""
            DELETE FROM documents
            WHERE id = %s
        """, (
            document_id,
        ))

        conn.commit()
        cur.close()

        return {
            "success": True,
            "id": document_id,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
