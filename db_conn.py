import os, psycopg2
from urllib.parse import urlparse

def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        u = urlparse(db_url)
        return psycopg2.connect(
            dbname=u.path.lstrip("/"),
            user=u.username,
            password=u.password,
            host=u.hostname,
            port=u.port,
            sslmode="require"   # Wichtig für Neon
        )
    return psycopg2.connect(
        dbname="JobScout",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5433"
    )