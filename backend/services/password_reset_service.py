from datetime import datetime, timedelta
from email.mime.text import MIMEText
import os
import secrets
import smtplib

from backend.config import (
    FRONTEND_URL,
    LDAP_BASE_DN,
    LDAP_DOMAIN,
    LDAP_ENABLED,
    LDAP_HOST,
    LDAP_PORT,
    MAIL_HOST,
    MAIL_PORT,
    MAIL_USERNAME,
)
from backend.database.connection import get_db_connection
from ldap3 import MODIFY_REPLACE, Connection, Server, Tls
from ldap3.utils.conv import escape_filter_chars
from werkzeug.security import generate_password_hash


def send_password_reset_email(to_email, token):
  try:
    frontend_url = os.getenv("FRONTEND_URL", "http://ortakportal.sirket.local")
    reset_url = f"{frontend_url}/reset-password/{token}"
    mail_user = os.getenv("MAIL_USERNAME", "testsirket0@gmail.com")
    mail_pass = os.getenv("GMAIL_APP_PASSWORD", "")
    mail_host = os.getenv("MAIL_HOST", "smtp.gmail.com")
    mail_port = int(os.getenv("MAIL_PORT", "587"))

    if not mail_user or not mail_pass:
      return False

    body = f"""Merhaba,

Company Portal hesabınız için şifre sıfırlama talebi oluşturuldu.
Yeni şifrenizi belirlemek için aşağıdaki bağlantıyı kullanın:

{reset_url}

Bu bağlantı 15 dakika boyunca geçerlidir.
Eğer bu işlemi siz yapmadıysanız bu e-postayı dikkate almayabilirsiniz.

Company Portal
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Company Portal - Şifre Sıfırlama"
    msg["From"] = f"Company Portal <{mail_user}>"
    msg["To"] = to_email

    s = smtplib.SMTP(mail_host, mail_port, timeout=10)
    s.starttls()
    s.login(mail_user, mail_pass)
    s.sendmail(mail_user, [to_email], msg.as_string())
    s.quit()
    print(f"Sifre sifirlama maili gonderildi: {to_email}")
    return True
  except Exception as e:
    print(f"Sifre sifirlama mail hatasi: {e}")
    return False


def request_password_reset(email):
  conn = get_db_connection()
  try:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username FROM users WHERE LOWER(email) = LOWER(%s) LIMIT 1",
        (email.strip(),),
    )
    user = cur.fetchone()
    if not user:
      return {
          "success": False,
          "error": "Bu e-posta adresiyle kayıtlı kullanıcı bulunamadı.",
      }

    user_id = user[0]
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    cur.execute(
        """
        INSERT INTO password_resets (user_id, token, expires_at, used)
        VALUES (%s, %s, %s, false)
        """,
        (user_id, token, expires_at),
    )
    conn.commit()
    cur.close()

    send_password_reset_email(email.strip(), token)
    return {
        "success": True,
        "message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.",
    }
  except Exception as e:
    conn.rollback()
    return {"success": False, "error": f"Bir hata oluştu: {e}"}
  finally:
    conn.close()


def reset_password_with_token(token, new_password):
  conn = get_db_connection()
  try:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pr.id, pr.user_id, u.username, u.email
        FROM password_resets pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.token = %s AND pr.expires_at > NOW() AND pr.used = false
        LIMIT 1
        """,
        (token,),
    )
    reset_req = cur.fetchone()
    if not reset_req:
      return False, "Geçersiz veya süresi dolmuş sıfırlama bağlantısı."

    reset_id, user_id, username, email = reset_req

    # 1. PostgreSQL veritabanında şifreyi güncelle
    cur.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (generate_password_hash(new_password), user_id),
    )
    cur.execute(
        "UPDATE password_resets SET used = true WHERE id = %s",
        (reset_id,),
    )
    conn.commit()

    # 2. OpenLDAP (company-ldap) üzerinde de şifreyi güncelle (Giriş buraya bakar!)
    try:
      s_ldap = Server(LDAP_HOST, port=LDAP_PORT, connect_timeout=5)
      c_ldap = Connection(
          s_ldap,
          user="cn=admin,dc=sirket,dc=local",
          password="AdminPassword123!",
          auto_bind=True,
      )
      if c_ldap.bound:
        c_ldap.modify(
            f"cn={username},ou=users,{LDAP_BASE_DN}",
            {"userPassword": [(MODIFY_REPLACE, [new_password])]},
        )
        print(f"OpenLDAP sifresi guncellendi: {username}")
    except Exception as ex:
      print(f"OpenLDAP sifre hatasi: {ex}")

    # 3. DC01 Active Directory üzerinde de şifreyi güncelle (varsa)
    try:
      import ssl

      s_dc = Server(
          "192.168.10.10",
          port=636,
          use_ssl=True,
          tls=Tls(validate=ssl.CERT_NONE),
          connect_timeout=5,
      )
      c_dc = None
      for pw in ["ays'ma123", "aysima123", "Aysima123!"]:
        try:
          conn_dc = Connection(
              s_dc,
              user=f"Administrator@{LDAP_DOMAIN}",
              password=pw,
              auto_bind=True,
          )
          if conn_dc.bound:
            c_dc = conn_dc
            break
        except Exception:
          continue
      if c_dc and c_dc.bound:
        safe_u = escape_filter_chars(username)
        c_dc.search(
            "DC=sirket,DC=local",
            f"(sAMAccountName={safe_u})",
            attributes=["distinguishedName"],
        )
        if c_dc.entries:
          dn = c_dc.entries[0].entry_dn
          unicode_pwd = ('"' + new_password + '"').encode("utf-16-le")
          c_dc.modify(dn, {"unicodePwd": [(MODIFY_REPLACE, [unicode_pwd])]})
          print(f"DC01 AD sifresi guncellendi: {username}")
    except Exception as ex:
      print(f"DC01 sifre hatasi: {ex}")

    return True, "Parolanız başarıyla güncellendi."
  except Exception as e:
    conn.rollback()
    return False, f"Hata: {e}"
  finally:
    cur.close()
    conn.close()