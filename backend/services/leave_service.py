# PostgreSQL bağlantısını merkezi database katmanından alıyoruz.
from backend.database.connection import get_db_connection


# =========================================================
# İZİN TALEBİ OLUŞTUR
# =========================================================

def create_leave_request(
    user_id,
    start_date,
    end_date,
    reason,
    attachment_name=None,
    attachment_object_name=None
):
    """
    Çalışan adına yeni bir izin talebi oluşturur.

    Business logic bu katmanda bulunur.
    Route katmanı yalnızca HTTP isteğini yönetir.
    """

    # PostgreSQL bağlantısı oluşturuyoruz.
    conn = get_db_connection()

    try:

        # SQL sorgularını çalıştırmak için cursor oluşturuyoruz.
        cur = conn.cursor()

        # -------------------------------------------------
        # ÇALIŞANIN YÖNETİCİSİNİ BUL
        # -------------------------------------------------

        # İzin talebinde yöneticiyi frontend'den almıyoruz.
        # Sistem kullanıcının manager_id alanından yöneticiyi
        # otomatik olarak belirliyor.
        cur.execute("""
            SELECT
                manager_id
            FROM users
            WHERE id = %s
        """, (
            user_id,
        ))

        user = cur.fetchone()

        # Kullanıcı bulunamadıysa izin oluşturamayız.
        if not user:

            return {
                "success": False,
                "error": "Çalışan bulunamadı."
            }

        manager_id = user[0]

        # Çalışanın yöneticisi tanımlı değilse
        # yönetici onay sürecini başlatamayız.
        if manager_id is None:

            return {
                "success": False,
                "error": (
                    "Bu çalışan için yönetici "
                    "tanımlanmamış."
                )
            }

        # -------------------------------------------------
        # İZİN TALEBİNİ OLUŞTUR
        # -------------------------------------------------

        # İlk aşamada izin talebi yöneticinin onayını bekliyor.
        cur.execute("""
            INSERT INTO leave_requests
            (
                user_id,
                start_date,
                end_date,
                reason,
                status,
                approval_stage,
                attachment_name,
                attachment_object_name
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'pending',
                'manager_pending',
                %s,
                %s
            )
            RETURNING id
        """, (
            user_id,
            start_date,
            end_date,
            reason,
            attachment_name,
            attachment_object_name
        ))

        # Oluşturulan izin kaydının ID'sini alıyoruz.
        leave_id = cur.fetchone()[0]

        # Transaction'ı onaylıyoruz.
        conn.commit()

        return {
            "success": True,
            "leave_id": leave_id,
            "manager_id": manager_id,
            "approval_stage": "manager_pending"
        }

    except Exception:

        # Hata oluşursa yapılan veritabanı değişikliklerini
        # geri alıyoruz.
        conn.rollback()

        raise

    finally:

        # Cursor ve database bağlantısını kapatıyoruz.
        cur.close()
        conn.close()


# =========================================================
# KENDİ İZİNLERİNİ GETİR
# =========================================================

def get_my_leave_requests(user_id):
    """
    Giriş yapan çalışanın kendi izin taleplerini getirir.

    user_id session üzerinden gelir.
    Böylece kullanıcı başka bir çalışanın ID'sini
    göndererek başka kişinin izinlerini göremez.
    """

    # PostgreSQL bağlantısı oluşturuyoruz.
    conn = get_db_connection()

    try:

        # SQL sorgularını çalıştırmak için cursor oluşturuyoruz.
        cur = conn.cursor()

        # Sadece giriş yapan çalışanın izinlerini getiriyoruz.
        # Yönetici bilgilerini de sorguya dahil ediyoruz.
        cur.execute("""
            SELECT
                lr.id,
                lr.start_date,
                lr.end_date,
                lr.reason,
                lr.status,
                lr.approval_stage,
                lr.admin_note,
                lr.created_at,
                lr.attachment_name,
                lr.manager_note,
                lr.hr_note,
                m.first_name AS manager_first_name,
                m.last_name AS manager_last_name
            FROM leave_requests lr
            LEFT JOIN users m
                ON lr.manager_reviewed_by = m.id
            WHERE lr.user_id = %s
            ORDER BY lr.created_at DESC
        """, (
            user_id,
        ))

        # Sorgudan dönen kayıtları alıyoruz.
        requests = cur.fetchall()

        # Cursor'ı kapatıyoruz.
        cur.close()

        return requests

    finally:

        # Hata olsa bile database bağlantısını kapatıyoruz.
        conn.close()
       
# =========================================================
# İZİN ONAYLA
# =========================================================

def approve_leave_request(
    request_id,
    reviewer_id,
    note=""
):
    """
    Bir izin talebini mevcut onay aşamasına göre onaylar.

    manager_pending aşamasında:
        Sadece çalışanın yöneticisi onaylayabilir.
        Sonraki aşama hr_pending olur.

    hr_pending aşamasında:
        Sadece İK onaylayabilir.
        Sonraki durum approved olur.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        # İzin talebini ve çalışanın yöneticisini getiriyoruz.
        cur.execute("""
            SELECT
                lr.user_id,
                lr.approval_stage,
                u.manager_id
            FROM leave_requests lr
            INNER JOIN users u
                ON lr.user_id = u.id
            WHERE lr.id = %s
        """, (
            request_id,
        ))

        leave = cur.fetchone()

        if not leave:

            return {
                "success": False,
                "error": "İzin talebi bulunamadı."
            }

        user_id = leave[0]
        approval_stage = leave[1]
        manager_id = leave[2]

        # -------------------------------------------------
        # YÖNETİCİ ONAYI
        # -------------------------------------------------

        if approval_stage == "manager_pending":

            # Talebi onaylayan kişinin,
            # çalışanın kayıtlı yöneticisi olması gerekiyor.
            if manager_id != reviewer_id:

                return {
                    "success": False,
                    "error": (
                        "Bu izin talebini onaylama "
                        "yetkiniz yok."
                    )
                }

            # Yönetici onayladıktan sonra
            # talep İK'nın önüne geçiyor.
            cur.execute("""
                UPDATE leave_requests
                SET
                    approval_stage = 'hr_pending',
                    manager_reviewed_by = %s,
                    manager_reviewed_at = CURRENT_TIMESTAMP,
                    manager_note = %s
                WHERE id = %s
            """, (
                reviewer_id,
                note,
                request_id
            ))

            conn.commit()

            return {
                "success": True,
                "approval_stage": "hr_pending"
            }

        # -------------------------------------------------
        # İK ONAYI
        # -------------------------------------------------

        if approval_stage == "hr_pending":

            # İK kontrolünü rol üzerinden yapıyoruz.
            cur.execute("""
                SELECT
                    role
                FROM users
                WHERE id = %s
            """, (
                reviewer_id,
            ))

            reviewer = cur.fetchone()

            if not reviewer:

                return {
                    "success": False,
                    "error": "Onaylayan kullanıcı bulunamadı."
                }

            reviewer_role = reviewer[0]

            if reviewer_role not in (
                "hr_admin",
                "admin"
            ):

                return {
                    "success": False,
                    "error": (
                        "Bu izin talebini İK olarak "
                        "onaylama yetkiniz yok."
                    )
                }

            # İK onayından sonra izin tamamlanıyor.
            cur.execute("""
                UPDATE leave_requests
                SET
                    status = 'approved',
                    approval_stage = 'completed',
                    hr_reviewed_by = %s,
                    hr_reviewed_at = CURRENT_TIMESTAMP,
                    hr_note = %s
                WHERE id = %s
            """, (
                reviewer_id,
                note,
                request_id
            ))

            conn.commit()

            return {
                "success": True,
                "approval_stage": "completed",
                "status": "approved"
            }

        return {
            "success": False,
            "error": "Bu izin talebi onaylanabilir durumda değil."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        conn.close()


# =========================================================
# İZİN REDDET
# =========================================================

def reject_leave_request(
    request_id,
    reviewer_id,
    note=""
):
    """
    İzin talebini mevcut onay aşamasına göre reddeder.

    Hem yönetici hem İK aşamasında çalışabilir.
    """

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        # İzin talebinin mevcut aşamasını ve
        # çalışanın yöneticisini buluyoruz.
        cur.execute("""
            SELECT
                lr.approval_stage,
                u.manager_id
            FROM leave_requests lr
            INNER JOIN users u
                ON lr.user_id = u.id
            WHERE lr.id = %s
        """, (
            request_id,
        ))

        leave = cur.fetchone()

        if not leave:

            return {
                "success": False,
                "error": "İzin talebi bulunamadı."
            }

        approval_stage = leave[0]
        manager_id = leave[1]

        # -------------------------------------------------
        # YÖNETİCİ REDDİ
        # -------------------------------------------------

        if approval_stage == "manager_pending":

            if manager_id != reviewer_id:

                return {
                    "success": False,
                    "error": (
                        "Bu izin talebini reddetme "
                        "yetkiniz yok."
                    )
                }

            cur.execute("""
                UPDATE leave_requests
                SET
                    status = 'rejected',
                    approval_stage = 'rejected',
                    manager_reviewed_by = %s,
                    manager_reviewed_at = CURRENT_TIMESTAMP,
                    manager_note = %s
                WHERE id = %s
            """, (
                reviewer_id,
                note,
                request_id
            ))

            conn.commit()

            return {
                "success": True,
                "status": "rejected",
                "approval_stage": "rejected"
            }

        # -------------------------------------------------
        # İK REDDİ
        # -------------------------------------------------

        if approval_stage == "hr_pending":

            cur.execute("""
                SELECT
                    role
                FROM users
                WHERE id = %s
            """, (
                reviewer_id,
            ))

            reviewer = cur.fetchone()

            if not reviewer:

                return {
                    "success": False,
                    "error": "Onaylayan kullanıcı bulunamadı."
                }

            if reviewer[0] not in (
                "hr_admin",
                "admin"
            ):

                return {
                    "success": False,
                    "error": (
                        "Bu izin talebini İK olarak "
                        "reddetme yetkiniz yok."
                    )
                }

            cur.execute("""
                UPDATE leave_requests
                SET
                    status = 'rejected',
                    approval_stage = 'rejected',
                    hr_reviewed_by = %s,
                    hr_reviewed_at = CURRENT_TIMESTAMP,
                    hr_note = %s
                WHERE id = %s
            """, (
                reviewer_id,
                note,
                request_id
            ))

            conn.commit()

            return {
                "success": True,
                "status": "rejected",
                "approval_stage": "rejected"
            }

        return {
            "success": False,
            "error": "Bu izin talebi reddedilebilir durumda değil."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        conn.close()

# =========================================================
# BEKLEYEN İZİNLERİ GETİR
# =========================================================

def get_pending_leave_requests(reviewer_id):
    """
    Giriş yapan kullanıcının onaylayabileceği
    bekleyen izin taleplerini getirir.

    Yönetici:
        Kendi çalışanlarının manager_pending izinlerini görür.

    HR:
        hr_pending izinlerini görür.

    Admin:
        Hem kendi çalışanlarının manager_pending izinlerini
        hem de hr_pending izinlerini görür.
    """

    conn = get_db_connection()
    cur = None

    try:
        cur = conn.cursor()

        # -------------------------------------------------
        # KULLANICININ ROLÜNÜ BUL
        # -------------------------------------------------

        cur.execute("""
            SELECT role
            FROM users
            WHERE id = %s
        """, (
            reviewer_id,
        ))

        reviewer = cur.fetchone()

        if not reviewer:
            return {
                "success": False,
                "error": "Kullanıcı bulunamadı."
            }

        reviewer_role = reviewer[0]

        # -------------------------------------------------
        # ADMIN
        # -------------------------------------------------

        if reviewer_role == "admin":
            cur.execute("""
                SELECT
                    lr.id,
                    u.id,
                    u.first_name,
                    u.last_name,
                    d.name AS department,
                    lr.start_date,
                    lr.end_date,
                    lr.reason,
                    lr.status,
                    lr.approval_stage,
                    lr.created_at
                FROM leave_requests lr
                INNER JOIN users u
                    ON lr.user_id = u.id
                LEFT JOIN departments d
                    ON u.department_id = d.id
                WHERE
                    (
                        lr.approval_stage = 'manager_pending'
                        AND u.manager_id = %s
                    )
                    OR
                    lr.approval_stage = 'hr_pending'
                ORDER BY lr.created_at ASC
            """, (
                reviewer_id,
            ))

        # -------------------------------------------------
        # HR
        # -------------------------------------------------

        elif reviewer_role == "hr_admin":
            cur.execute("""
                SELECT
                    lr.id,
                    u.id,
                    u.first_name,
                    u.last_name,
                    d.name AS department,
                    lr.start_date,
                    lr.end_date,
                    lr.reason,
                    lr.status,
                    lr.approval_stage,
                    lr.created_at
                FROM leave_requests lr
                INNER JOIN users u
                    ON lr.user_id = u.id
                LEFT JOIN departments d
                    ON u.department_id = d.id
                WHERE
                    lr.approval_stage = 'hr_pending'
                ORDER BY lr.created_at ASC
            """)

        # -------------------------------------------------
        # NORMAL YÖNETİCİ
        # -------------------------------------------------

        else:
            cur.execute("""
                SELECT
                    lr.id,
                    u.id,
                    u.first_name,
                    u.last_name,
                    d.name AS department,
                    lr.start_date,
                    lr.end_date,
                    lr.reason,
                    lr.status,
                    lr.approval_stage,
                    lr.created_at
                FROM leave_requests lr
                INNER JOIN users u
                    ON lr.user_id = u.id
                LEFT JOIN departments d
                    ON u.department_id = d.id
                WHERE
                    lr.approval_stage = 'manager_pending'
                    AND u.manager_id = %s
                ORDER BY lr.created_at ASC
            """, (
                reviewer_id,
            ))

        requests = cur.fetchall()

        return {
            "success": True,
            "requests": requests
        }

    finally:
        if cur:
            cur.close()

        conn.close()

# =========================================================
# ADMIN / İK İÇİN TÜM İZİN TALEPLERİ
# =========================================================

def get_all_leave_requests():
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                lr.id,
                lr.user_id,
                u.first_name,
                u.last_name,
                COALESCE(d.name, u.department) AS department,
                lr.start_date,
                lr.end_date,
                lr.reason,
                lr.status,
                lr.approval_stage,
                lr.admin_note,
                lr.manager_note,
                lr.hr_note,
                lr.created_at
            FROM leave_requests lr
            INNER JOIN users u
                ON lr.user_id = u.id
            LEFT JOIN departments d
                ON u.department_id = d.id
            ORDER BY
                CASE
                    WHEN lr.status = 'pending'
                    THEN 0
                    ELSE 1
                END,
                lr.created_at DESC
        """)

        rows = cur.fetchall()
        cur.close()

        return rows

    finally:
        conn.close()
