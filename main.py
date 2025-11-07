from core.orchestrator import load_params
from core.normalizer import normalize_jobs
from core.schema import Job, CommonQuery
from core.db_conn import get_conn

from datetime import datetime
import os
import psycopg2
import hashlib

# DB-Upsert Funktion - FIXED: Return inserted count
def upsert_jobs(jobs: list[Job], cursor, conn) -> int:
    """
    Speichert normalisierte Jobs in PostgreSQL.
    Returns: Anzahl der tatsächlich eingefügten Jobs
    """
    inserted_count = 0
    
    for job in jobs:
        raw_str = f"{job.title}-{job.company}-{job.location}-{job.source}-{job.id}-{job.job_type}-{job.remote}"
        hash_value = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        
        print(f"[DB] Attempting insert: {job.title} | {job.company} ({job.source})")
        
        try:
            cursor.execute("""
                INSERT INTO jobs (source, title, company, location, job_type, work_mode, posted_at, url, hash_value)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (hash_value) DO NOTHING
                RETURNING id
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
            
            # Check if row was actually inserted
            result = cursor.fetchone()
            if result:
                inserted_count += 1
                print(f"  ✓ Inserted (ID: {result[0]})")
            else:
                print(f"  ⊘ Skipped (duplicate)")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"  ✗ Error: {e}")
    
    return inserted_count

def normalize_job_types(cursor, conn):
    """
    Normalisiert job_type Werte nach dem Einfügen.
    Ersetzt englische Begriffe durch deutsche.
    """
    print("→ Normalizing job_type values...")
    
    normalization_sql = """
        UPDATE public.jobs
        SET job_type = CASE
    WHEN job_type IN ('Full-Time', 'full_time', 'Full-time', 'Full-time permanent') THEN 'Vollzeit'
    WHEN job_type IN ('Half-Time', 'half_time', 'Part-Time', 'Part-time', 'part_time' ) THEN 'Teilzeit'
    WHEN job_type IN ('Full-time permanent, experienced') THEN 'Vollzeit unbefristet, erfahren'
    WHEN job_type IN ('Full-time permanent, mid') THEN 'Vollzeit unbefristet, mittleres Erfahrungsniveau'
    WHEN job_type IN ('Working student, berufseinstieg') THEN 'Werkstudent, Berufseinsteiger'
    WHEN job_type = 'berufseinstieg' THEN 'Berufseinsteiger'
    WHEN job_type LIKE '%Internship%' THEN 'Praktikum'
    WHEN job_type IN ('contract', 'Contract') THEN 'Vertrag'
    WHEN job_type = 'freelance' THEN 'Freelancer'
    WHEN job_type = 'Apprenticeship' THEN 'Ausbildung'
    WHEN job_type = 'Working student' THEN 'Werkstudent'
    ELSE job_type
    END;
    """
    
    try:
        cursor.execute(normalization_sql)
        rows_updated = cursor.rowcount
        conn.commit()
        print(f"  ✓ Normalized {rows_updated} job_type values\n")
        return rows_updated
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error normalizing job_type: {e}\n")
        return 0


# Optional: Run logging
USE_RUN_TABLE = os.getenv("USE_RUN_TABLE") == "1"

def _log_run_start(cur, conn):
    if not USE_RUN_TABLE:
        return None
    try:
        cur.execute("""
            INSERT INTO ingestion_runs (rows_total, rows_inserted) 
            VALUES (0,0) 
            RETURNING id
        """)
        rid = cur.fetchone()[0]
        conn.commit()
        return rid
    except Exception as e:
        print(f"Warning: Could not log run start: {e}")
        return None

def _log_run_end(cur, conn, run_id, rows_total, rows_inserted, error):
    if not USE_RUN_TABLE or run_id is None:
        return
    try:
        cur.execute("""
            UPDATE ingestion_runs 
            SET finished_at=now(), rows_total=%s, rows_inserted=%s, error=%s 
            WHERE id=%s
        """, (rows_total, rows_inserted, error, run_id))
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not log run end: {e}")


def main():
    """Main ingestion function"""
    print(f"\n{'='*60}")
    print(f"JobScout Daily Ingestion - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    conn = None
    cur = None
    run_id = None
    
    try:
        # 1. Connect to database
        print("→ Connecting to database...")
        conn = get_conn()
        cur = conn.cursor()
        print("  ✓ Connected\n")
        
        # 2. Optional: Log run start
        run_id = _log_run_start(cur, conn)
        
        # 3. Fetch jobs from APIs
        print("→ Fetching jobs from APIs...")
        common_params = CommonQuery(
            category="IT",
            limit=100
        )
        all_raws = load_params(common_params)
        print(f"  ✓ API calls completed\n")
        
        # 4. Normalize jobs
        print("→ Normalizing jobs...")
        all_normalized = normalize_jobs(all_raws)
        print(f"  ✓ Normalized {len(all_normalized)} jobs\n")
        
        if len(all_normalized) == 0:
            print("⚠ Warning: No jobs to insert!\n")
            _log_run_end(cur, conn, run_id, 0, 0, "No jobs fetched")
            return
        
        # 5. Show sample
        print("→ Sample jobs:")
        for j in all_normalized[:3]:
            print(f"  • {j.title} - {j.company} ({j.source})")
        if len(all_normalized) > 3:
            print(f"  ... and {len(all_normalized) - 3} more\n")
        else:
            print()
        
        # 6. Insert into database
        print("→ Inserting into database...")
        rows_inserted = upsert_jobs(all_normalized, cur, conn)
        print(f"  ✓ Inserted {rows_inserted} new jobs (skipped {len(all_normalized) - rows_inserted} duplicates)\n")
        
        # 7. Log success
        _log_run_end(cur, conn, run_id, len(all_normalized), rows_inserted, None)
        
        print(f"{'='*60}")
        print(f"✓ SUCCESS - {rows_inserted}/{len(all_normalized)} jobs added to database")
        print(f"{'='*60}\n")
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        print(f"\n{'='*60}")
        print(f"✗ ERROR - Ingestion failed")
        print(f"{'='*60}")
        print(f"Error: {error_msg}\n")
        
        if cur and conn:
            _log_run_end(cur, conn, run_id, 0, 0, error_msg)
        
        raise  # Re-raise to make GitHub Actions show as failed
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("→ Database connection closed\n")


if __name__ == "__main__":
    main()