# core/db_conn.py
# ──────────────────────────────────────────────
# Einheitliche Datenbankverbindung (PostgreSQL Neon)
# ──────────────────────────────────────────────

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Neon-Verbindungs-URL aus Env-Variable laden
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Fehler: DATABASE_URL ist nicht gesetzt.")

# Sicherstellen, dass sslmode=require gesetzt ist
if "sslmode=" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

# Einfacher Connection Pool (für Slackbot & Producer)
POOL_MIN = int(os.environ.get("DB_POOL_MIN", "1"))
POOL_MAX = int(os.environ.get("DB_POOL_MAX", "5"))
pool = SimpleConnectionPool(POOL_MIN, POOL_MAX, dsn=DATABASE_URL)

def get_conn():
    """Gibt eine DB-Verbindung aus dem Pool zurück."""
    return pool.getconn()

def put_conn(conn):
    """Gibt eine DB-Verbindung zurück in den Pool."""
    if conn:
        pool.putconn(conn)
