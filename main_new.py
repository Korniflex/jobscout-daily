from core.orchestrator import load_params
from core.normalizer import normalize_jobs
from core.schema import Job, CommonQuery
from core.db_conn import get_conn
from adapters import get_params_remotive,fetch_remotive,get_params_agentur, fetch_agentur, get_params_arbeitnow, fetch_arbeitnow ,get_params_jobicy, fetch_jobicy

from datetime import datetime
import pandas as pd
import os

import psycopg2
import hashlib
from dotenv import load_dotenv
load_dotenv()

# Neon Database Verbindung:
conn = get_conn()
cursor = conn.cursor()


# DB-Upsert Funktion:
def upsert_jobs(jobs: list[Job]):
    """
    Speichert normalisierte Jobs in PostgreSQL.
    - Deduplikation über hash_value (Titel, Firma, Ort, Source, ID und Arbeitsmodus)
    - Einzel-Commit pro Job, Rollback bei Fehler
    """
    for job in jobs:
        # baut einen eindeutigen String aus Jobtitel, Firma, Ort, Source, ID und Arbeitsmodus
        raw_str = f"{job.title}-{job.company}-{job.location}-{job.source}-{job.id}-{job.job_type}-{job.remote}"
        hash_value = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()    # erzeugt daraus einen Fingerabdruck (Hash), also eine eindeutige ID
        print(f"[DB] inserting : {job.title} | {job.company}, {job.source}")
        try:
            cursor.execute("""
                INSERT INTO jobs (source, title, company, location, job_type, work_mode, posted_at, url, hash_value)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s)
                ON CONFLICT (hash_value) DO NOTHING
            """, (                                 # ON CONFLICT DO NOTHING => wenn dieser Wert schon existiert -> nicht doppelt einfügen. Wir nutzen DO NOTHING, weil wir doppelte Jobs nicht mehrfach speichern wollen. Also einmal in die DB -> später, wenn der gleiche Job nochmal auftaucht, wird er übersprungen.
                job.source or "",
                job.title or "",
                job.company or "",
                job.location or "",
                job.job_type or "",
                job.remote or "",
                job.posted_at or None,
                str(job.url) if job.url else "",  # <- hier wandeln wir HttpUrl in String um. Denn Pydantic verwendet für URLs häufig den Typ HttpUrl. PostgreSQL über psycopg2 kann HttpUrl nicht automatisch in TEXT konvertieren. Das bedeutet: psycopg2 weiß nicht, wie es ein HttpUrl-Objekt in die Datenbank schreiben soll
                hash_value
            ))
            conn.commit()

        except Exception as e:
            # conn.rollback() einfügen, wenn ein Fehler passiert:
            conn.rollback()
            print(f"Fehler bei {job.title} @ {job.company} ({job.job_type}): {e}")
            # Wenn beim INSERT ein Fehler passiert (zB doppelter Schlüssel, falscher Datentyp), bricht PostgreSQL die aktuelle Transaktion ab
            # rollback setzt nur die fehlerhafte Transaktion zurück. Danach kann das Skript weiterlaufen und die nächsten Jobs einfügen!


# Macht dieser TEIL ueberhaupt Sinn?
IT_SYNONYMS = [
    "IT", "Informatik", "Software", "Softwareentwicklung", "Tech", "Technology",
    "Software & IT", "Computer Science", "Entwicklung", "Developer", "Engineering"
]

def main():


    common_params = CommonQuery(
        search=None,               
        category="IT",
        category_synonyms=IT_SYNONYMS,
        company=None,
        posted_since=None,
        work_mode=None,
        remote=None, 
        location=None,                         
        limit=100,
    ) 


    all_raws= load_params(common_params)
    all_normalized= normalize_jobs(all_raws)

    print(f"Gesamt normalisierte Jobs: {len(all_normalized)}")
    for j in all_normalized[:5]:
        print(j.title, "-", j.company, "-", j.url, f"({j.source})")

    # DB Upsert:
    upsert_jobs(all_normalized)

# --- Run logging for the daily cron ---
def _log_run_start(cur, conn) -> int:
    cur.execute("INSERT INTO ingestion_runs (rows_total, rows_inserted) VALUES (0,0) RETURNING id;")
    run_id = cur.fetchone()[0]
    conn.commit()
    return run_id

def _log_run_end(cur, conn, run_id: int, rows_total: int, rows_inserted: int, error: str | None):
    cur.execute(
        "UPDATE ingestion_runs SET finished_at=now(), rows_total=%s, rows_inserted=%s, error=%s WHERE id=%s;",
        (rows_total, rows_inserted, error, run_id)
    )
    conn.commit()

if __name__ == "__main__":
    conn = get_conn()
    cur = conn.cursor()
    run_id = _log_run_start(cur, conn)

    try:
        # your current job-fetching logic
        all_raws = load_params(CommonQuery())
        all_normalized = normalize_jobs(all_raws)

        print(f"Total normalized jobs: {len(all_normalized)}")
        for j in all_normalized[:5]:
            print(j.title, "-", j.company, "-", j.url, f"({j.source})")

        rows_inserted = upsert_jobs(all_normalized)
        _log_run_end(cur, conn, run_id, len(all_normalized), rows_inserted or 0, None)
    except Exception as e:
        _log_run_end(cur, conn, run_id, 0, 0, str(e))
        raise
    finally:
        cur.close()
        conn.close()
