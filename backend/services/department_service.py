from backend.database.connection import get_db_connection
from backend.config import ALLOWED_DEPARTMENTS


def get_all_departments():
    """
    Portalda kullanılmasına izin verilen departmanları getirir.
    """

    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                name,
                parent_id
            FROM departments
            WHERE name = ANY(%s)
            ORDER BY
                CASE name
                    WHEN 'Bilgi Teknolojileri' THEN 1
                    WHEN 'Finans' THEN 2
                    WHEN 'İnsan Kaynakları' THEN 3
                    ELSE 4
                END
            """,
            (
                list(ALLOWED_DEPARTMENTS),
            )
        )

        departments = cur.fetchall()

        cur.close()

        return departments

    finally:
        conn.close()
