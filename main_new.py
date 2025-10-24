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
        raw_str = f"{job.title}-{job.company}-{job.location}-{job.source}-{job.id}-{job.job_type}-{job.source}"
        hash_value = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()    # erzeugt daraus einen Fingerabdruck (Hash), also eine eindeutige ID
        print(f"[DB] inserting : {job.title} | {job.company}")
        try:
            cursor.execute("""
                INSERT INTO jobs (source, title, company, location, job_type, posted_at, url, hash_value)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (hash_value) DO NOTHING
            """, (                                 # ON CONFLICT DO NOTHING => wenn dieser Wert schon existiert -> nicht doppelt einfügen. Wir nutzen DO NOTHING, weil wir doppelte Jobs nicht mehrfach speichern wollen. Also einmal in die DB -> später, wenn der gleiche Job nochmal auftaucht, wird er übersprungen.
                job.source or "",
                job.title or "",
                job.company or "",
                job.location or "",
                job.job_type or "",
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

########################################################################################
#Temporäres Excel File
    print(f"Gesamt normalisierte Jobs: {len(all_normalized)}")
    for j in all_normalized[:5]:
        print(j.title, "|", j.company, "|", j.location, "|", j.remote, "|",  j.url)
    
    
    os.makedirs("exports", exist_ok=True)  # Herstellt file falls nötig

    out_file = f"exports/{datetime.now().strftime('%Y%m%d')}_Jobs_sammlung.xlsx"
    pd.DataFrame([j.model_dump() for j in all_normalized]).to_excel(out_file, index=False)
    print("Exportiert nach:", out_file)

##############################################################################################
if __name__ == "__main__":
    main()
    cursor.close()
    conn.close()

