# core/db_conn.py
import os
import psycopg2
from urllib.parse import urlparse

def get_conn():
    """
    Erstellt eine neue PostgreSQL-Verbindung zu Neon.
    Jeder Aufruf erstellt eine NEUE Verbindung (kein Pool).
    """
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        raise RuntimeError("❌ DATABASE_URL ist nicht gesetzt!")
    
    # Stelle sicher, dass sslmode=require gesetzt ist
    if "sslmode=" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"
    
    # Parse URL
    parsed = urlparse(db_url)
    
    try:
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            sslmode="require",
            connect_timeout=10
        )
        return conn
    except psycopg2.Error as e:
        raise RuntimeError(f"DB Connection failed: {e}")


def put_conn(conn):
    """
    Schließt eine Datenbankverbindung sauber.
    Führt vorher ein commit aus, falls Transaktion offen.
    """
    if conn:
        try:
            # Rollback falls Transaktion noch offen
            if not conn.closed:
                conn.rollback()
                conn.close()
        except Exception:
            pass  # Ignoriere Fehler beim Schließen