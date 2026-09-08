import logging

import json

import redis

from backend.database.connection import get_db_connection


# Redis bağlantısını oluşturuyoruz.
redis_client = redis.Redis(
    host="company-redis",
    port=6379,
    decode_responses=True
)



logger = logging.getLogger(__name__)

def get_announcements(role, department):
    """
    Duyuruları getirir.

    Admin:
        Tüm duyuruları görür.

    Diğer kullanıcılar:
        Genel + kendi departmanlarına ait duyuruları görür.
    """

    cache_key = "announcements"

    try:

        cached = redis_client.get(
            cache_key
        )

        if cached:

            all_announcements = json.loads(
                cached
            )

        else:

            all_announcements = None

    except redis.RedisError as error:

        print(
            "Redis okuma hatası:",
            error
        )

        all_announcements = None

    # Redis'te kayıt yoksa PostgreSQL'den alıyoruz.
    if all_announcements is None:

        conn = get_db_connection()

        try:

            cur = conn.cursor()

            cur.execute("""
                SELECT
                    announcements.id,
                    announcements.title,
                    announcements.content,
                    announcements.created_at,
                    users.username,
                    announcements.department
                FROM announcements
                LEFT JOIN users
                    ON announcements.created_by = users.id
                ORDER BY announcements.created_at DESC
            """)

            rows = cur.fetchall()

            cur.close()

        finally:

            conn.close()

        all_announcements = []

        for row in rows:

            all_announcements.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": (
                    row[3].isoformat()
                    if row[3]
                    else None
                ),
                "created_by": row[4],
                "department": row[5]
            })

        # Duyuruları Redis'e yazıyoruz.
        try:

            redis_client.set(
                cache_key,
                json.dumps(
                    all_announcements,
                    ensure_ascii=False
                )
            )

        except redis.RedisError as error:

            print(
                "Redis yazma hatası:",
                error
            )

    # Admin tüm duyuruları görebilir.
    if role == "admin":

        return all_announcements

    # Diğer kullanıcılar sadece kendilerini ilgilendiren
    # duyuruları görüyor.
    return [
        announcement
        for announcement in all_announcements
        if (
            announcement["department"] == "Genel"
            or announcement["department"] == department
        )
    ]


def create_announcement(
    title,
    content,
    department,
    created_by
):
    """
    Yeni duyuru oluşturur.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("""
            INSERT INTO announcements
            (
                title,
                content,
                created_by,
                department
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            title,
            content,
            created_by,
            department
        ))

        announcement_id = cur.fetchone()[0]

        conn.commit()

        cur.close()

        # Yeni kayıt oluşturulduğu için
        # eski Redis cache'ini temizliyoruz.
        clear_announcement_cache()

        return {
            "success": True,
            "id": announcement_id
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def clear_announcement_cache():
    """
    Duyuru cache'ini temizler.
    """

    try:

        redis_client.delete(
            "announcements"
        )

    except redis.RedisError as error:

        print(
            "Redis cache temizleme hatası:",
            error
        )
def update_announcement(
    announcement_id,
    title,
    content,
    department
):
    """
    Mevcut duyuruyu günceller.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        # Önce kaydın mevcut olup olmadığını kontrol ediyoruz.
        cur.execute("""
            SELECT id
            FROM announcements
            WHERE id = %s
        """, (
            announcement_id,
        ))

        announcement = cur.fetchone()

        if not announcement:
            cur.close()

            return {
                "success": False,
                "error": "Duyuru bulunamadı."
            }

        cur.execute("""
            UPDATE announcements
            SET
                title = %s,
                content = %s,
                department = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            title,
            content,
            department,
            announcement_id
        ))

        conn.commit()

        cur.close()

        # Cache artık eski veriyi tutmamalı.
        clear_announcement_cache()

        return {
            "success": True,
            "id": announcement_id
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def delete_announcement(
    announcement_id
):
    """
    Mevcut duyuruyu siler.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("""
            DELETE FROM announcements
            WHERE id = %s
            RETURNING id
        """, (
            announcement_id,
        ))

        deleted = cur.fetchone()

        if not deleted:

            conn.rollback()

            cur.close()

            return {
                "success": False,
                "error": "Duyuru bulunamadı."
            }

        conn.commit()

        cur.close()

        clear_announcement_cache()

        return {
            "success": True,
            "id": deleted[0]
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()