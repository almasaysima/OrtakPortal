import psycopg

from backend.config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)


def get_db_connection():
    """
    Uygulamanın merkezi PostgreSQL bağlantı noktası.
    Bağlantı bilgileri environment variable üzerinden okunur.
    """

    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
