import json
import re
import requests
from datetime import datetime
from core.schema import Job


arbeitnow_url = 'https://www.arbeitnow.com/api/job-board-api'

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
            return jobs  # FIX: war vorher "return []"
        return []
    except Exception as e:
        print("Error Arbeitnow:", e)
        return []


def normalize_arbeitnow(job: dict) -> Job:
    # job_types ist oft eine Liste, manchmal String
    jtypes = job.get("job_types") or job.get("job_type") or []
    if isinstance(jtypes, str):
        jtypes = [jtypes]
    jt = ", ".join([s for s in jtypes if s]) or None

    # remote kann bool, string oder über job_types kommen
    remote_flag = job.get("remote")
    remote_mode = None
    if isinstance(remote_flag, bool):
        remote_mode = "remote" if remote_flag else None
    elif isinstance(remote_flag, str):
        if remote_flag.strip().lower() in {"true", "yes", "1"}:
            remote_mode = "remote"
    if not remote_mode and jt:
        jl = jt.lower()
        if "remote" in jl:
            remote_mode = "remote"
        elif "hybrid" in jl:
            remote_mode = "hybrid"

    return {
        "id": f"arbeitnow:{job.get('id') or job.get('slug')}",
        "source": "arbeitnow",
        "title": job.get("title"),
        "company": job.get("company_name"),
        # Fallback-Kette für Ort
        "location": job.get("location") or job.get("candidate_required_location"),
        "url": job.get("url"),
        "posted_at": (
            datetime.fromtimestamp(job["created_at"]).isoformat()
            if isinstance(job.get("created_at"), (int, float))
            else job.get("created_at")
        ),
        "job_type": jt,            # <- jetzt gesetzt
        "remote": remote_mode,     # <- jetzt gesetzt (wird zu work_mode in DB)
    }


def normalize_arbeitnow_list(rows: list[dict]) -> list[Job]:
    return [normalize_arbeitnow(j) for j in rows]