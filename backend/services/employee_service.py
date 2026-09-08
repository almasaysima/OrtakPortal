# PostgreSQL bağlantısını merkezi database katmanından alıyoruz.
from backend.database.connection import get_db_connection


def search_employees(search_text):
    """
    Çalışanları ad, soyad veya e-posta üzerinden arar.

    Bu fonksiyon HTTP isteğini doğrudan karşılamaz.
    Çalışan arama iş mantığını yürüttüğü için
    service katmanında bulunur.
    """

    # Kullanıcının gönderdiği arama metnindeki
    # gereksiz boşlukları temizliyoruz.
    search_text = search_text.strip()

    # Arama metni çok kısa veya boşsa
    # gereksiz veritabanı sorgusu yapmıyoruz.
    if len(search_text) < 2:
        return []

    # PostgreSQL bağlantısı oluşturuyoruz.
    conn = get_db_connection()

    try:

        # Veritabanı sorgularını çalıştırmak için
        # cursor oluşturuyoruz.
        cur = conn.cursor()

        # =====================================================
        # ÇALIŞAN ARAMA SORGUSU
        # =====================================================
        #
        # u  -> aradığımız çalışan
        # d  -> çalışanın departmanı
        # m  -> çalışanın yöneticisi
        #
        # "users" tablosunu ikinci kez kullanmamız
        # self join olarak adlandırılır.
        #
        # Örneğin:
        # Ayşe.manager_id = 1
        # users.id = 1
        # olan kullanıcı yöneticisi olur.

        cur.execute("""
            SELECT
                u.id,
                u.first_name,
                u.last_name,
                u.email,
                d.name AS department,
                u.manager_id,
                m.first_name AS manager_first_name,
                m.last_name AS manager_last_name

            FROM users u

            LEFT JOIN departments d
                ON u.department_id = d.id

            LEFT JOIN users m
                ON u.manager_id = m.id

            WHERE
                u.first_name ILIKE %s
                OR u.last_name ILIKE %s
                OR u.email ILIKE %s

            ORDER BY
                u.first_name,
                u.last_name

            LIMIT 20;
        """, (
            f"%{search_text}%",
            f"%{search_text}%",
            f"%{search_text}%"
        ))

        # SQL sorgusundan dönen tüm çalışanları alıyoruz.
        employees = cur.fetchall()

        # Cursor'ı kapatıyoruz.
        cur.close()

        # Sonuçları route katmanına gönderiyoruz.
        return employees

    finally:

        # Hata oluşsa bile veritabanı bağlantısının
        # açık kalmasını önlüyoruz.
        conn.close()