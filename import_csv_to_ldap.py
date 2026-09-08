import csv
from ldap3 import ALL, Connection, Server

print("1. LDAP Sunucusuna baglaniliyor...")
s = Server("company-ldap", port=389, get_info=ALL)
c = Connection(
    s,
    user="cn=admin,dc=sirket,dc=local",
    password="AdminPassword123!",
    auto_bind=True,
)
print("-> Baglanti basarili!")

# OU Yapilari
c.add("ou=users,dc=sirket,dc=local", ["top", "organizationalUnit"])
c.add("ou=groups,dc=sirket,dc=local", ["top", "organizationalUnit"])

# Tum Gruplarin Olusturulmasi
groups = [
    "OrtakPortal-GenelAdmin",
    "OrtakPortal-IT-Yonetici",
    "OrtakPortal-IT-Calisan",
    "OrtakPortal-IK-Yonetici",
    "OrtakPortal-IK-Calisan",
    "OrtakPortal-Finans-Yonetici",
    "OrtakPortal-Finans-Calisan",
]

for g in groups:
  c.add(
      f"cn={g},ou=groups,dc=sirket,dc=local",
      ["top", "groupOfNames"],
      {"member": ["cn=admin,dc=sirket,dc=local"]},
  )

# CSV Dosyasini Oku ve LDAP'a Yaz
with open("/app/calisanlar.csv", "r", encoding="utf-8") as f:
  reader = csv.DictReader(f)
  for row in reader:
    u = row["username"].strip()
    fn = row["first_name"].strip()
    ln = row["last_name"].strip()
    email = row["email"].strip()
    pwd = row["password"].strip()
    grp = row["role_group"].strip()
    dn = f"cn={u},ou=users,dc=sirket,dc=local"

    # Kullanici Ekle (Varsa gec)
    c.add(
        dn,
        ["top", "person", "organizationalPerson", "inetOrgPerson"],
        {
            "sn": ln,
            "givenName": fn,
            "displayName": f"{fn} {ln}",
            "mail": email,
            "userPassword": pwd,
        },
    )

    # Gruba Ekle
    c.modify(
        f"cn={grp},ou=groups,dc=sirket,dc=local",
        {"member": [("MODIFY_ADD", [dn])]},
    )
    print(f"+ LDAP'a Eklendi: {u} ({fn} {ln}) -> {grp}")

print("\nTum sirket hiyerarsisi CSV'den LDAP'a basariyla aktarildi!")