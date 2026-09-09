import os
import smtplib
from email.mime.text import MIMEText

# PostgreSQL bağlantısını merkezi database katmanından alıyoruz.
from backend.database.connection import get_db_connection


# =========================================================
# E-POSTA BILDIRIM YARDIMCISI (SIRKET MAILI ILE GONDERIM)
# =========================================================

def send_leave_notification_email(leave_id, status_text, note=""):
  try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT u.email, u.first_name, u.last_name, lr.start_date, lr.end_date, lr.reason
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.id
            WHERE lr.id = %s
        """,
        (leave_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
      return

    to_email, first_name, last_name, start_date, end_date, reason = row

    mail_user = os.getenv("MAIL_USERNAME", "testsirket0@gmail.com")
    mail_pass = os.getenv("GMAIL_APP_PASSWORD", "")
    mail_host = os.getenv("MAIL_HOST", "smtp.gmail.com")
    mail_port = int(os.getenv("MAIL_PORT", "587"))

    if not mail_user or not mail_pass:
      print("Mail kullanici adi veya sifresi tanimli degil.")
      return

    subject = f"İzin Talebi Durumu: {status_text.upper()}"
    body = f"""Sayın {first_name} {last_name},

{start_date} - {end_date} tarihleri arasındaki izin talebiniz şirket yönetimi tarafından {status_text.upper()}.

İzin Gerekçeniz: {reason}
Yönetici Notu: {note if note else '-'}

Bilgilerinize sunarız.
OrtakPortal Şirket Yönetimi
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"OrtakPortal Şirket Yönetimi <{mail_user}>"
    msg["To"] = to_email

    s = smtplib.SMTP(mail_host, mail_port, timeout=10)
    s.starttls()
    s.login(mail_user, mail_pass)
    s.sendmail(mail_user, [to_email], msg.as_string())
    s.quit()
    print(f"İzin bildirim maili gönderildi: {to_email} ({status_text})")
  except Exception as e:
    print(f"İzin mail gönderme hatası: {e}")


# =========================================================
# İZİN TALEBİ OLUŞTUR
# =========================================================


def create_leave_request(
    user_id,
    start_date,
    end_date,
    reason,
    attachment_name=None,
    attachment_object_name=None,
):
  conn = get_db_connection()
  try:
    cur = conn.cursor()

    cur.execute(
        """
            SELECT manager_id
            FROM users
            WHERE id = %s
        """,
        (user_id,),
    )
    user = cur.fetchone()

    if not user:
      return {"success": False, "error": "Çalışan bulunamadı."}

    manager_id = user[0]

    if manager_id is None:
      return {
          "success": False,
          "error": "Bu çalışan için yönetici tanımlanmamış.",
      }

    cur.execute(
        """
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
                %s, %s, %s, %s, 'pending', 'manager_pending', %s, %s
            )
            RETURNING id
        """,
        (
            user_id,
            start_date,
            end_date,
            reason,
            attachment_name,
            attachment_object_name,
        ),
    )

    leave_id = cur.fetchone()[0]
    conn.commit()

    return {
        "success": True,
        "leave_id": leave_id,
        "manager_id": manager_id,
        "approval_stage": "manager_pending",
    }

  except Exception:
    conn.rollback()
    raise
  finally:
    cur.close()
    conn.close()


# =========================================================
# KENDİ İZİNLERİNİ GETİR
# =========================================================


def get_my_leave_requests(user_id):
  conn = get_db_connection()
  try:
    cur = conn.cursor()
    cur.execute(
        """
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
        """,
        (user_id,),
    )
    requests = cur.fetchall()
    cur.close()
    return requests
  finally:
    conn.close()


# =========================================================
# İZİN ONAYLA
# =========================================================


def approve_leave_request(request_id, reviewer_id, note=""):
  conn = get_db_connection()
  try:
    cur = conn.cursor()
    cur.execute(
        """
            SELECT
                lr.user_id,
                lr.approval_stage,
                u.manager_id
            FROM leave_requests lr
            INNER JOIN users u
                ON lr.user_id = u.id
            WHERE lr.id = %s
        """,
        (request_id,),
    )
    leave = cur.fetchone()

    if not leave:
      return {"success": False, "error": "İzin talebi bulunamadı."}

    user_id = leave[0]
    approval_stage = leave
    manager_id = leave

    # 1. Aşama: Yönetici Onayı
    if approval_stage == "manager_pending":
      if manager_id != reviewer_id:
        return {
            "success": False,
            "error": "Bu izin talebini onaylama yetkiniz yok.",
        }

      cur.execute(
          """
                UPDATE leave_requests
                SET
                    approval_stage = 'hr_pending',
                    manager_reviewed_by = %s,
                    manager_reviewed_at = CURRENT_TIMESTAMP,
                    manager_note = %s
                WHERE id = %s
            """,
          (reviewer_id, note, request_id),
      )
      conn.commit()

      # E-posta bildirimi gönder (Yönetici onayladı, İK onayı bekliyor)
      send_leave_notification_email(
          request_id, "Yöneticiniz Tarafından Onaylandı (İK Onayı Bekliyor)", note
      )

      return {"success": True, "approval_stage": "hr_pending"}

    # 2. Aşama: İK Onayı
    if approval_stage == "hr_pending":
      cur.execute(
          """
                SELECT role
                FROM users
                WHERE id = %s
            """,
          (reviewer_id,),
      )
      reviewer = cur.fetchone()

      if not reviewer:
        return {
            "success": False,
            "error": "Onaylayan kullanıcı bulunamadı.",
        }

      reviewer_role = reviewer[0]
      if reviewer_role not in ("hr_admin", "admin"):
        return {
            "success": False,
            "error": "Bu izin talebini İK olarak onaylama yetkiniz yok.",
        }

      cur.execute(
          """
                UPDATE leave_requests
                SET
                    status = 'approved',
                    approval_stage = 'completed',
                    hr_reviewed_by = %s,
                    hr_reviewed_at = CURRENT_TIMESTAMP,
                    hr_note = %s
                WHERE id = %s
            """,
          (reviewer_id, note, request_id),
      )
      conn.commit()

      # E-posta bildirimi gönder (Tamamen ONAYLANDI)
      send_leave_notification_email(request_id, "ONAYLANDI", note)

      return {
          "success": True,
          "approval_stage": "completed",
          "status": "approved",
      }

    return {
        "success": False,
        "error": "Bu izin talebi onaylanabilir durumda değil.",
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


def reject_leave_request(request_id, reviewer_id, note=""):
  conn = get_db_connection()
  try:
    cur = conn.cursor()
    cur.execute(
        """
            SELECT
                lr.approval_stage,
                u.manager_id
            FROM leave_requests lr
            INNER JOIN users u
                ON lr.user_id = u.id
            WHERE lr.id = %s
        """,
        (request_id,),
    )
    leave = cur.fetchone()

    if not leave:
      return {"success": False, "error": "İzin talebi bulunamadı."}

    approval_stage = leave[0]
    manager_id = leave

    # Yönetici Reddi
    if approval_stage == "manager_pending":
      if manager_id != reviewer_id:
        return {
            "success": False,
            "error": "Bu izin talebini reddetme yetkiniz yok.",
        }

      cur.execute(
          """
                UPDATE leave_requests
                SET
                    status = 'rejected',
                    approval_stage = 'rejected',
                    manager_reviewed_by = %s,
                    manager_reviewed_at = CURRENT_TIMESTAMP,
                    manager_note = %s
                WHERE id = %s
            """,
          (reviewer_id, note, request_id),
      )
      conn.commit()

      # E-posta bildirimi gönder (Yönetici reddetti)
      send_leave_notification_email(
          request_id, "Yöneticiniz Tarafından REDDEDİLDİ", note
      )

      return {
          "success": True,
          "status": "rejected",
          "approval_stage": "rejected",
      }

    # İK Reddi
    if approval_stage == "hr_pending":
      cur.execute(
          """
                SELECT role
                FROM users
                WHERE id = %s
            """,
          (reviewer_id,),
      )
      reviewer = cur.fetchone()

      if not reviewer:
        return {
            "success": False,
            "error": "Onaylayan kullanıcı bulunamadı.",
        }

      if reviewer[0] not in ("hr_admin", "admin"):
        return {
            "success": False,
            "error": "Bu izin talebini İK olarak reddetme yetkiniz yok.",
        }

      cur.execute(
          """
                UPDATE leave_requests
                SET
                    status = 'rejected',
                    approval_stage = 'rejected',
                    hr_reviewed_by = %s,
                    hr_reviewed_at = CURRENT_TIMESTAMP,
                    hr_note = %s
                WHERE id = %s
            """,
          (reviewer_id, note, request_id),
      )
      conn.commit()

      # E-posta bildirimi gönder (İK reddetti)
      send_leave_notification_email(
          request_id, "İK Tarafından REDDEDİLDİ", note
      )

      return {
          "success": True,
          "status": "rejected",
          "approval_stage": "rejected",
      }

    return {
        "success": False,
        "error": "Bu izin talebi reddedilebilir durumda değil.",
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
  conn = get_db_connection()
  cur = None
  try:
    cur = conn.cursor()
    cur.execute(
        """
            SELECT role
            FROM users
            WHERE id = %s
        """,
        (reviewer_id,),
    )
    reviewer = cur.fetchone()

    if not reviewer:
      return {"success": False, "error": "Kullanıcı bulunamadı."}

    reviewer_role = reviewer[0]

    if reviewer_role == "admin":
      cur.execute(
          """
                SELECT
                    lr.id,
                    lr.user_id,
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
            """,
          (reviewer_id,),
      )
    elif reviewer_role == "hr_admin":
      cur.execute("""
                SELECT
                    lr.id,
                    lr.user_id,
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
    else:
      cur.execute(
          """
                SELECT
                    lr.id,
                    lr.user_id,
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
            """,
          (reviewer_id,),
      )

    requests = cur.fetchall()
    return {"success": True, "requests": requests}
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