# Kommentare im Code auf Deutsch
import os
import psycopg2

def get_conn():
    # 1) Bevorzugt: vollständige DSN-URL aus der Umgebung (Neon "pooled")
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        # WICHTIG: DSN unverändert an psycopg2 übergeben.
        # Keine eigene Zerlegung per urlparse, damit keine Query-Parameter verloren gehen.
        return psycopg2.connect(
            dsn,
            connect_timeout=10,
            application_name="jobscout-slackbot"
        )

    # 2) Fallback: lokale Dev-DB
    return psycopg2.connect(
        dbname="JobScout",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5433"
    )
