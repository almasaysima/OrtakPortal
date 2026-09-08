from backend.database.connection import get_db_connection


def get_events(role, department):
    """
    Etkinlikleri getirir.

    Admin:
        Tüm etkinlikleri görür.

    Diğer kullanıcılar:
        Genel + kendi departmanlarına ait etkinlikleri görür.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        if role == "admin":

            cur.execute("""
                SELECT
                    events.id,
                    events.title,
                    events.description,
                    events.event_date,
                    events.location,
                    users.username,
                    events.department
                FROM events
                LEFT JOIN users
                    ON events.created_by = users.id
                ORDER BY events.event_date ASC
            """)

        else:

            cur.execute("""
                SELECT
                    events.id,
                    events.title,
                    events.description,
                    events.event_date,
                    events.location,
                    users.username,
                    events.department
                FROM events
                LEFT JOIN users
                    ON events.created_by = users.id
                WHERE
                    events.department = 'Genel'
                    OR events.department = %s
                ORDER BY events.event_date ASC
            """, (
                department,
            ))

        rows = cur.fetchall()

        cur.close()

        events = []

        for row in rows:

            events.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "event_date": (
                    row[3].isoformat()
                    if row[3]
                    else None
                ),
                "location": row[4],
                "created_by": row[5],
                "department": row[6]
            })

        return events

    finally:

        conn.close()


def create_event(
    title,
    description,
    event_date,
    location,
    department,
    created_by
):
    """
    Yeni etkinlik oluşturur.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("""
            INSERT INTO events
            (
                title,
                description,
                event_date,
                location,
                created_by,
                department
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
        """, (
            title,
            description,
            event_date,
            location,
            created_by,
            department
        ))

        event_id = cur.fetchone()[0]

        conn.commit()

        cur.close()

        return {
            "success": True,
            "id": event_id
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def update_event(
    event_id,
    title,
    description,
    event_date,
    location,
    department
):
    """
    Mevcut etkinliği günceller.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM events
            WHERE id = %s
        """, (
            event_id,
        ))

        event = cur.fetchone()

        if not event:

            cur.close()

            return {
                "success": False,
                "error": "Etkinlik bulunamadı."
            }

        cur.execute("""
            UPDATE events
            SET
                title = %s,
                description = %s,
                event_date = %s,
                location = %s,
                department = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            title,
            description,
            event_date,
            location,
            department,
            event_id
        ))

        conn.commit()

        cur.close()

        return {
            "success": True,
            "id": event_id
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def delete_event(event_id):
    """
    Mevcut etkinliği siler.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("""
            DELETE FROM events
            WHERE id = %s
            RETURNING id
        """, (
            event_id,
        ))

        deleted = cur.fetchone()

        if not deleted:

            conn.rollback()

            cur.close()

            return {
                "success": False,
                "error": "Etkinlik bulunamadı."
            }

        conn.commit()

        cur.close()

        return {
            "success": True,
            "id": deleted[0]
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()