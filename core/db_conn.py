# core/db_conn.py
import os
import psycopg2
from urllib.parse import urlparse

def get_conn():
    """Erstellt eine neue DB-Verbindung zu Neon PostgreSQL."""
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        raise RuntimeError("DATABASE_URL ist nicht gesetzt!")
    
    # Parse URL und stelle sicher, dass sslmode=require gesetzt ist
    parsed = urlparse(db_url)
    
    return psycopg2.connect(
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        sslmode="require"
    )

def put_conn(conn):
    """Schließt eine DB-Verbindung (für Kompatibilität mit Pool-Interface)."""
    if conn:
        conn.close()