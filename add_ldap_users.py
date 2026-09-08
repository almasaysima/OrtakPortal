from backend.services.auth_service import authenticate_ldap
from ldap3 import ALL, Connection, Server

print("1. LDAP Sunucusuna baglaniliyor...")
s = Server("company-ldap", port=389, get_info=ALL)
c = Connection(
    s,
    user="cn=admin,dc=sirket,dc=local",
    password="AdminPassword123!",
    auto_bind=True,
)
print("-> Admin baglantisi:", c.bound)

# 1. OU Ekleme
c.add("ou=users,dc=sirket,dc=local", ["top", "organizationalUnit"])
c.add("ou=groups,dc=sirket,dc=local", ["top", "organizationalUnit"])

# 2. Test Kullanicisi: aysimaalmas (Sifre: LdapSifre123!)
c.add(
    "cn=aysimaalmas,ou=users,dc=sirket,dc=local",
    ["top", "person", "organizationalPerson", "inetOrgPerson"],
    {
        "sn": "Almas",
        "givenName": "Aysima",
        "displayName": "Aysima Almas",
        "mail": "aysima@sirket.local",
        "userPassword": "LdapSifre123!",
    },
)
print("-> aysimaalmas eklendi:", c.result.get("description"))

# 3. Grup: OrtakPortal-IT-Calisan
c.add(
    "cn=OrtakPortal-IT-Calisan,ou=groups,dc=sirket,dc=local",
    ["top", "groupOfNames"],
    {"member": ["cn=aysimaalmas,ou=users,dc=sirket,dc=local"]},
)
print("-> IT-Calisan grubu eklendi:", c.result.get("description"))

# 4. Canli Test: authenticate_ldap fonksiyonunu cagir
print("\n2. Portalin LDAP giris fonksiyonu test ediliyor...")
res = authenticate_ldap("aysimaalmas", "LdapSifre123!")
print("-> LDAP DOGRULAMA SONUCU:", res)