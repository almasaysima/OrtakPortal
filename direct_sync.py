from backend.database.connection import get_db_connection
from ldap3 import ALL, Connection, Server, SUBTREE
from werkzeug.security import generate_password_hash

print("1. Departmanlar kontrol ediliyor...")
conn = get_db_connection()
cur = conn.cursor()

depts = {
    "Bilgi Teknolojileri": "IT",
    "İnsan Kaynakları": "HR",
    "Finans": "FIN",
    "Genel": "GEN",
}
dept_map = {}
for dname in depts:
  cur.execute("SELECT id FROM departments WHERE name = %s", (dname,))
  row = cur.fetchone()
  if row:
    dept_map[dname] = row[0]
  else:
    cur.execute(
        "INSERT INTO departments (name) VALUES (%s) RETURNING id", (dname,)
    )
    dept_map[dname] = cur.fetchone()[0]
conn.commit()

print("2. LDAP'tan kullanicilar okunup veritabanina aktariliyor...")
s = Server("company-ldap", port=389)
c = Connection(
    s,
    user="cn=admin,dc=sirket,dc=local",
    password="AdminPassword123!",
    auto_bind=True,
)
c.search(
    "ou=users,dc=sirket,dc=local",
    "(objectClass=person)",
    search_scope=SUBTREE,
    attributes=["cn", "givenName", "sn", "displayName", "mail"],
)

group_role_map = {
    "OrtakPortal-GenelAdmin": ("admin", "Genel"),
    "OrtakPortal-IT-Yonetici": ("it_admin", "Bilgi Teknolojileri"),
    "OrtakPortal-IT-Calisan": ("employee", "Bilgi Teknolojileri"),
    "OrtakPortal-Finans-Yonetici": ("finance_admin", "Finans"),
    "OrtakPortal-Finans-Calisan": ("employee", "Finans"),
    "OrtakPortal-IK-Yonetici": ("hr_admin", "İnsan Kaynakları"),
    "OrtakPortal-IK-Calisan": ("employee", "İnsan Kaynakları"),
}

for e in c.entries:
  u = e.cn.value
  c.search(
      "ou=groups,dc=sirket,dc=local",
      f"(member={e.entry_dn})",
      search_scope=SUBTREE,
      attributes=["cn"],
  )
  groups = [g.cn.value for g in c.entries]
  role = "employee"
  dept_name = "Bilgi Teknolojileri"
  for g in groups:
    if g in group_role_map:
      role, dept_name = group_role_map[g]
      break

  dept_id = dept_map.get(dept_name)
  fn = (
      e.givenName.value
      if hasattr(e, "givenName") and e.givenName.value
      else u.split(".")[0].capitalize()
  )
  ln = (
      e.sn.value
      if hasattr(e, "sn") and e.sn.value
      else (u.split(".").capitalize() if "." in u else "Personel")
  )
  mail = (
      e.mail.value
      if hasattr(e, "mail") and e.mail.value
      else f"{u}@sirket.local"
  )
  pwd_hash = generate_password_hash("LdapSifre123!")

  cur.execute(
      """
        INSERT INTO users (username, email, password_hash, first_name, last_name, role, department_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (username) DO UPDATE
        SET email = EXCLUDED.email,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            role = EXCLUDED.role,
            department_id = EXCLUDED.department_id
    """,
      (u, mail, pwd_hash, fn, ln, role, dept_id),
  )
  print(f"+ Eklendi/Guncellendi: {u} ({fn} {ln}) -> {role} | {dept_name}")

conn.commit()

print("\n3. Yoneticiler departmanlara ve calisanlara baglaniyor...")
cur.execute("""
    UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'elayilmaz') WHERE name = 'Bilgi Teknolojileri';
    UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'selin.kaya') WHERE name = 'İnsan Kaynakları';
    UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'burak.sahin') WHERE name = 'Finans';

    UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'elayilmaz') WHERE department_id = (SELECT id FROM departments WHERE name = 'Bilgi Teknolojileri') AND username != 'elayilmaz';
    UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'selin.kaya') WHERE department_id = (SELECT id FROM departments WHERE name = 'İnsan Kaynakları') AND username != 'selin.kaya';
    UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'burak.sahin') WHERE department_id = (SELECT id FROM departments WHERE name = 'Finans') AND username != 'burak.sahin';
""")
conn.commit()
conn.close()
print("\n-> TUM SIRKET KULLANICILARI VE HIYERARSI PORTAL VERITABANINA AKTARILDI!")