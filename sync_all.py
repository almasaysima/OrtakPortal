from backend.database.connection import get_db_connection
from backend.services.auth_service import GROUP_ROLE_MAP, sync_ad_user
from ldap3 import ALL, Connection, Server, SUBTREE

print("1. Departmanlar veritabaninda kontrol ediliyor...")
conn = get_db_connection()
cur = conn.cursor()

# Temel Departmanlar (Sadece name alanı)
depts = ["Bilgi Teknolojileri", "İnsan Kaynakları", "Finans", "Genel"]

for dname in depts:
  cur.execute("SELECT id FROM departments WHERE name = %s", (dname,))
  if not cur.fetchone():
    cur.execute("INSERT INTO departments (name) VALUES (%s)", (dname,))
    print(f"+ Yeni departman eklendi: {dname}")

conn.commit()
print("-> Departmanlar hazir!")

print("\n2. LDAP sunucusundan kullanicilar cekilip senkronize ediliyor...")
s = Server("company-ldap", port=389, get_info=ALL)
c = Connection(
    s,
    user="cn=admin,dc=sirket,dc=local",
    password="AdminPassword123!",
    auto_bind=True,
)

# Tum kullanicilari tara
c.search(
    "ou=users,dc=sirket,dc=local",
    "(objectClass=person)",
    search_scope=SUBTREE,
    attributes=["cn", "givenName", "sn", "displayName", "mail"],
)

for entry in c.entries:
  u = entry.cn.value
  attrs = entry.entry_attributes_as_dict

  # Kullanicinin gruplarini bul
  c.search(
      "ou=groups,dc=sirket,dc=local",
      f"(member={entry.entry_dn})",
      search_scope=SUBTREE,
      attributes=["cn"],
  )
  groups = [g.cn.value for g in c.entries]

  # Role ve Departmani belirle
  role = "employee"
  dept = "Bilgi Teknolojileri"
  for g in groups:
    if g in GROUP_ROLE_MAP:
      role = GROUP_ROLE_MAP[g]["role"]
      dept = GROUP_ROLE_MAP[g]["department"]
      break

  ad_user = {
      "username": u,
      "email": (
          attrs.get("mail", [f"{u}@sirket.local"])[0]
          if attrs.get("mail")
          else f"{u}@sirket.local"
      ),
      "role": role,
      "department": dept,
  }

  res = sync_ad_user(ad_user)
  print(f"+ Senkronize edildi: {u} -> Rol: {role} | Departman: {dept}")

# 3. Yoneticileri Otomatik Bagla
print("\n3. Yonetici - Calisan iliskileri kuruluyor...")
try:
  cur.execute("""
        UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'elayilmaz') 
        WHERE department_id = (SELECT id FROM departments WHERE name = 'Bilgi Teknolojileri') AND username != 'elayilmaz';
        UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'selin.kaya') 
        WHERE department_id = (SELECT id FROM departments WHERE name = 'İnsan Kaynakları') AND username != 'selin.kaya';
        UPDATE users SET manager_id = (SELECT id FROM users WHERE username = 'burak.sahin') 
        WHERE department_id = (SELECT id FROM departments WHERE name = 'Finans') AND username != 'burak.sahin';
        UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'elayilmaz') WHERE name = 'Bilgi Teknolojileri';
        UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'selin.kaya') WHERE name = 'İnsan Kaynakları';
        UPDATE departments SET manager_id = (SELECT id FROM users WHERE username = 'burak.sahin') WHERE name = 'Finans';
    """)
  conn.commit()
except Exception as ex:
  print(f"Yonetici baglama uyarisi: {ex}")

conn.close()
print("\n-> TUM SIRKET HIYERARSISI PORTAL VERITABANINA AKTARILDI!")