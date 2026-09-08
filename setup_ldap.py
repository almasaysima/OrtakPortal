import os
import re

print("1. OpenLDAP icine test kullanicisi ve gruplar ekleniyor...")
add_script = """
from ldap3 import Server, Connection, ALL
s = Server('company-ldap', port=389, get_info=ALL)
c = Connection(s, user='cn=admin,dc=sirket,dc=local', password='AdminPassword123!', auto_bind=True)

# OU (Organizasyon Birimleri)
c.add('ou=users,dc=sirket,dc=local', ['top', 'organizationalUnit'])
c.add('ou=groups,dc=sirket,dc=local', ['top', 'organizationalUnit'])

# Test Kullanicisi: aysimaalmas (Sifre: LdapSifre123!)
c.add('cn=aysimaalmas,ou=users,dc=sirket,dc=local', 
      ['top', 'person', 'organizationalPerson', 'inetOrgPerson'], 
      {'sn': 'Almas', 'givenName': 'Aysima', 'displayName': 'Aysima Almas', 'mail': 'aysima@sirket.local', 'userPassword': 'LdapSifre123!'})

# Gruplar: OrtakPortal-IT-Calisan
c.add('cn=OrtakPortal-IT-Calisan,ou=groups,dc=sirket,dc=local', 
      ['top', 'groupOfNames'], 
      {'member': 'cn=aysimaalmas,ou=users,dc=sirket,dc=local'})

c.add('cn=OrtakPortal-IT-Yonetici,ou=groups,dc=sirket,dc=local', 
      ['top', 'groupOfNames'], 
      {'member': 'cn=admin,dc=sirket,dc=local'})

print('-> LDAP kullanici ve gruplari basariyla olusturuldu!')
"""

os.system(f'docker exec -i company-backend python -c "{add_script}"')

print("2. auth_service.py evrensel LDAP formatina guncelleniyor...")
path = "backend/services/auth_service.py"
if os.path.exists(path):
  with open(path, "r", encoding="utf-8") as f:
    text = f.read()

  # Evrensel bind (Hem AD UPN hem OpenLDAP DN)
  old_bind_pattern = (
      r'bind_user\s*=\s*f\"\{username\}@\{LDAP_DOMAIN\}\"[\s\S]*?receive_timeout=5,\s*\)'
  )
  new_bind = """connection = None
        candidates = [
            f"{username}@{LDAP_DOMAIN}",
            f"cn={username},ou=users,{LDAP_BASE_DN}",
            f"uid={username},ou=users,{LDAP_BASE_DN}",
            f"cn={username},{LDAP_BASE_DN}"
        ]
        for u in candidates:
            try:
                c = Connection(server, user=u, password=password, auto_bind=True, receive_timeout=5)
                connection = c
                break
            except Exception:
                continue
        if not connection:
            return None"""
  text = re.sub(old_bind_pattern, new_bind, text)

  # Evrensel arama filtresi
  text = re.sub(
      r'\(&\(objectClass=user\)\s*f\"\(sAMAccountName=\{safe_username\}\)\"\)',
      'f"(|(sAMAccountName={safe_username})(cn={safe_username})(uid={safe_username}))"',
      text,
  )

  # OpenLDAP grup sorgusu destegi
  old_memberof = 'member_of = attributes.get(\n            "memberOf",\n            [],\n        )'
  new_memberof = """member_of = attributes.get("memberOf", [])
        if not member_of:
            try:
                user_dn = entry.entry_dn
                connection.search(search_base=LDAP_BASE_DN, search_filter=f"(member={user_dn})", attributes=["cn"])
                member_of = [f"cn={g.cn.value},ou=groups,{LDAP_BASE_DN}" for g in connection.entries]
            except Exception:
                pass"""
  text = text.replace(old_memberof, new_memberof)

  with open(path, "w", encoding="utf-8") as f:
    f.write(text)

  os.system(
      f"docker cp {path} company-backend:/app/backend/services/auth_service.py"
  )
  print("-> auth_service.py basariyla guncellendi!")