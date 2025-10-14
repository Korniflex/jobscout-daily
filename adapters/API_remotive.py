import json
import requests
from core.schema import Job


remotive_url = "https://remotive.com/api/remote-jobs"

def get_params_remotive(search: str = "", 
            category: str = "", 
            company: str = "", 
            location: str="",
            posted_since: str = "",
            work_mode: str = "",
            remote: str = "",
            limit: str = "",
            page: str = "",
            ) -> dict:

    params :dict= {}
    if search and search.strip():
        params["search"] = search.strip()
    if category and category.strip():
        params["category"] = category.strip()
    if company and company.strip():
        params["company_name"] = company.strip()
    if location and location.strip():
        params["candidate_required_location"] = location.strip()
    if posted_since and posted_since.strip():
        params["publication_date"] = posted_since.strip()
    if work_mode and work_mode.strip():
        params["job_type"] = work_mode.strip()
    if remote and remote.strip():
        params['remote'] = remote.strip() 
    if limit:
        params["limit"] = limit
    if page:
        params['page'] = page
    return params


def fetch_remotive(params: dict) -> list[dict]:

    try:
        r = requests.get(remotive_url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        jobs = data.get("jobs", [])
        print(f"  remotive_raw: {len(jobs)} jobs gefunden")
        if jobs:
            print(f"    Besipiel: {jobs[0].get('title')}")
        return jobs
    except Exception as e:
        print("Error Remotive:", e)
        return []
    
def normalize_remotive(job: dict) -> Job:
    
    jt = (job.get("job_type") or "").strip() or None
    loc = (job.get("candidate_required_location") or job.get("location") or None)
   
    loc_lower = str(loc).lower() if loc else ""
    is_remote = (
        (jt and "remote" in jt.lower()) or
        ("anywhere" in loc_lower) or
        ("remote" in loc_lower)
    )
    remote_mode = "remote" if is_remote else None

    return {
        "id": f"remotive:{job.get('id')}",
        "source": "remotive",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": loc,
        "job_type": jt,
        "remote": remote_mode,
        "url": job.get("url"),
        "posted_at": job.get("publication_date"),
    }

def normalize_remotive_list(rows: list[dict]) -> list[Job]:
    return [normalize_remotive(j) for j in rows]