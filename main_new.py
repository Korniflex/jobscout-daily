from core.orchestrator import load_params
from core.normalizer import normalize_jobs
from core.schema import Job, CommonQuery
from core.db_conn import get_conn, put_conn

from datetime import datetime
import pandas as pd
import os
import psycopg2
import hashlib
from dotenv import load_dotenv

load_dotenv()

def upsert_jobs(jobs: list[Job]):
    """
    Speichert normalisierte Jobs in PostgreSQL.
    - Deduplikation über hash_value
    - Einzel-Commit pro Job, Rollback bei Fehler
    """
    conn = get_conn()
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    errors = 0
    
    for job in jobs:
        raw_str = f"{job.title}-{job.company}-{job.location}-{job.source}-{job.id}-{job.job_type}"
        hash_value = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        
        try:
            cursor.execute("""
                INSERT INTO jobs (source, title, company, location, job_type, remote, posted_at, url, hash_value)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (hash_value) DO NOTHING
            """, (
                job.source or "",
                job.title or "",
                job.company or "",
                job.location or "",
                job.job_type or "",
                job.remote or "",
                job.posted_at or None,
                str(job.url) if job.url else "",
                hash_value
            ))
            
            if cursor.rowcount > 0:
                inserted += 1
                print(f"[DB] ✓ {job.title} @ {job.company}")
            else:
                skipped += 1
                
            conn.commit()

        except Exception as e:
            conn.rollback()
            errors += 1
            print(f"[DB] ✗ Fehler bei {job.title}: {e}")
    
    cursor.close()
    put_conn(conn)
    
    print(f"\n[DB] Summary: {inserted} neu, {skipped} übersprungen, {errors} Fehler")
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


def main():
    print("=" * 60)
    print("JobScout Backend - Job Collector")
    print("=" * 60)
    
    # KORRIGIERT: Kein category_synonyms mehr
    common_params = CommonQuery(
        search=None,               
        category="IT",
        company=None,
        posted_since=None,
        work_mode=None,
        location=None,                         
        limit=100,
    ) 

    print("\n[1/3] Fetching jobs from APIs...")
    all_raws = load_params(common_params)
    
    print(f"\n[2/3] Normalizing jobs...")
    all_normalized = normalize_jobs(all_raws)
    print(f"      Total normalized: {len(all_normalized)}")
    
    if all_normalized:
        print("\n      Sample jobs:")
        for j in all_normalized[:3]:
            print(f"      - {j.title} @ {j.company} ({j.source})")

    print(f"\n[3/3] Upserting to database...")
    stats = upsert_jobs(all_normalized)

    # Excel Export (optional, nur wenn Daten vorhanden)
    if all_normalized:
        try:
            os.makedirs("exports", exist_ok=True)
            out_file = f"exports/{datetime.now().strftime('%Y%m%d')}_Jobs.xlsx"
            pd.DataFrame([j.model_dump() for j in all_normalized]).to_excel(out_file, index=False)
            print(f"\n[Excel] Exported to: {out_file}")
        except Exception as e:
            print(f"[Excel] Export failed: {e}")

    print("\n" + "=" * 60)
    print(f"JobScout Backend Complete - {stats['inserted']} new jobs")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n!!! FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)