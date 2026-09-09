def set_dc01_ad_password(username, new_password):
  try:
    server = Server("192.168.10.10", port=389, connect_timeout=5)
    admin_conn = None

    # Her iki olasi DC01 sifresini de dene:
    for pw in ["ays'ma123", "aysima123", "Aysima123!"]:
      try:
        c = Connection(
            server,
            user=f"Administrator@{LDAP_DOMAIN}",
            password=pw,
            auto_bind=True,
            receive_timeout=5,
        )
        if c.bound:
          admin_conn = c
          break
      except Exception:
        continue

    if not admin_conn:
      print("DC01 Admin baglanamadi!")
      return False

    safe_u = escape_filter_chars(username)
    admin_conn.search(
        search_base="DC=sirket,DC=local",
        search_filter=f"(|(sAMAccountName={safe_u})(cn={safe_u}))",
        search_scope=SUBTREE,
        attributes=["entryDN"],
    )
    if admin_conn.entries:
      user_dn = admin_conn.entries[0].entry_dn
      unicode_pass = ('"' + new_password + '"').encode("utf-16-le")
      admin_conn.modify(
          user_dn, {"unicodePwd": [(MODIFY_REPLACE, [unicode_pass])]}
      )
      print(
          f"DC01 Sifresi Degisti ({username}):"
          f" {admin_conn.result.get('description')}"
      )
      return admin_conn.result.get("description") == "success"
  except Exception as ex:
    print(f"DC01 Sifre Guncelleme Hatasi: {ex}")
  return False