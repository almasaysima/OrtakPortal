from backend.database.connection import get_db_connection
from backend.services.auth_service import GROUP_ROLE_MAP, sync_ad_user
from ldap3 import ALL, Connection, Server, SUBTREE

print("1. Departmanlar kontrol ediliyor...")
conn = get_db_connection()
cur = conn.cursor()

for dname in ["Bilgi Teknolojileri", "İnsan Kaynakları", "Finans", "Genel"]:
  cur.execute("SELECT id FROM departments WHERE name = %s", (dname,))
  if not cur.fetchone():
    cur.execute("INSERT INTO departments (name) VALUES (%s)", (dname,))
    print(f"+ Departman eklendi: {dname}")
conn.commit()

print("\n2. LDAP kullanicilari veritabanina senkronize ediliyor...")
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
    attributes=["cn", "displayName", "mail"],
)

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
  dept = "Bilgi Teknolojileri"
  for g in groups:
    if g in GROUP_ROLE_MAP:
      role = GROUP_ROLE_MAP[g]["role"]
      dept = GROUP_ROLE_MAP[g]["department"]
      break

  mail = (
      e.mail.value
      if hasattr(e, "mail") and e.mail.value
      else f"{u}@sirket.local"
  )
  ad_user = {"username": u, "email": mail, "role": role, "department": dept}

  res = sync_ad_user(ad_user)
  print(f"+ Aktarildi: {u} -> Rol: {role} | Departman: {dept}")

print("\n3. Departman yoneticileri baglaniyor...")
try:
  cur.execute("""
        UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'elayilmaz') WHERE name = 'Bilgi Teknolojileri';
        UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'selin.kaya') WHERE name = 'İnsan Kaynakları';
        UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'burak.sahin') WHERE name = 'Finans';
        UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'elayilmaz') WHERE department_id = (SELECT id FROM departments WHERE name = 'Bilgi Teknolojileri') AND username != 'elayilmaz';
        UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'selin.kaya') WHERE department_id = (SELECT id FROM departments WHERE name = 'İnsan Kaynakları') AND username != 'selin.kaya';
        UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'burak.sahin') WHERE department_id = (SELECT id FROM departments WHERE name = 'Finans') AND username != 'burak.sahin';
    """)
  conn.commit()
  print("-> Yoneticiler basariyla baglandi!")
except Exception as ex:
  print(f"Yonetici baglama uyarisi: {ex}")

conn.close()
print("\n-> ISLEM TAMAMLANDI!")