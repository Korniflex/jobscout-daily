import json
import re
import requests
from datetime import datetime
from core.schema import Job


arbeitnow_url = 'https://www.arbeitnow.com/api/job-board-api'

def _strip_parens(text):
    """Entfernt alles in runden Klammern, überflüssige Leerzeichen
    und ggf. Ortsangaben am Ende des Titels."""
    if not text:
        return text
    # Entfernt Text in runden Klammern, z. B. "(m/w/d)"
    text = re.sub(r"\s*\([^)]*\)", "", str(text))
    # Entfernt doppelte Leerzeichen
    text = re.sub(r"\s{2,}", " ", text)
    # Entfernt "in [Ort]" am Ende des Titels (z. B. "Manager in Berlin" → "Manager")
    text = re.sub(r"\s+in\s+[A-ZÄÖÜ][a-zäöüß\- ]+$", "", text)
    return text.strip()

def get_params_arbeitnow(search: str = "", 
            category: str = "", 
            company: str = "", 
            location: str="",
            posted_since: str = "",
            work_mode: str = "",
            remote : str = "",
            page: int = 0,
            limit : int = "",
            ) -> dict:

    params :dict= {}

    if search and search.strip():
        params["search"] = search.strip()
    if category and category.strip():
        params["category"] = category.strip()
    if company and company.strip():
        params["company_name"] = company.strip()
    if location and location.strip():
        params["location"] = location.strip()
    if posted_since and posted_since.strip():
        params["created_at"] = posted_since.strip()
    if work_mode and work_mode.strip():
        params["job_types"] = work_mode.strip()
    if remote and remote.strip():
        params["remote"] = remote.strip()
    if page:
        params["page"] = page
    if limit:
        params["limit"]= limit
    return params

def fetch_arbeitnow(params: dict) -> list[dict]:
    try:
        r = requests.get(arbeitnow_url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json() or {}
        jobs = data.get("data") or data.get("jobs")
        print(f"  Arbeitnow_raw: {len(jobs)} jobs gefunden")
        if jobs:
            return jobs
    except Exception as e:
        print("Error Arbeitnow:", e)
        return []


def normalize_arbeitnow(job: dict) -> Job:
    # job_types ist oft eine liste
    jtypes = job.get("job_types") or []
    if isinstance(jtypes, str):
        jtypes = [jtypes]
    jt = ", ".join([s for s in jtypes if s]) or None

    # remote = bool 
    remote_flag = job.get("remote")
    remote_mode = None
    if isinstance(remote_flag, bool):
        remote_mode = "remote" if remote_flag else None
    elif jt:
        jt_lower = jt.lower()
        if "remote" in jt_lower:
            remote_mode = "remote"
        elif "hybrid" in jt_lower:
            remote_mode = "hybrid"

    # fallback location
    loc = job.get("candidate_required_location") or job.get("location") or None

    # posted_at int timestamp oder ISO
    created = job.get("created_at")
    if isinstance(created, (int, float)):
        try:
            created_iso = datetime.fromtimestamp(created).isoformat()
        except Exception:
            created_iso = None
    else:
        created_iso = created

    #  ID: "arbeitnow:<id>"
    job_id = job.get("id")
    if not job_id:
        slug_or_url = (job.get("slug") or job.get("url") or "").strip()
        m = re.search(r"(\d+)(?:/?$)", slug_or_url) 
        if m:
            job_id = m.group(1)
        else:
            job_id = slug_or_url.rstrip("/").split("/")[-1] if slug_or_url else "unknown"
    else:
        job_id = str(job_id).strip()

           # Titel bereinigen (ohne Klammern, etc.)


    return {
        "id": f"arbeitnow:{job_id}",
        "source": "arbeitnow",
        "title": "title",
        "company": job.get("company_name"),
        "location": loc,
        "job_type": jt,
        "remote": remote_mode,
        "url": job.get("url"),
        "posted_at": created_iso,
    }

def normalize_arbeitnow_list(rows: list[dict]) -> list[Job]:
    return [normalize_arbeitnow(j) for j in rows]
