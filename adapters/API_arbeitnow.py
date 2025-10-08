import json
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
    r = requests.get(arbeitnow_url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json() or {}
    jobs = data.get("data") or data.get("jobs")
    return jobs if isinstance(jobs, list) else []


def normalize_arbeitnow(job: dict) -> Job:
    return {
        "id": f"arbeitnow:{job.get('id')or job.get('slug')}",
        "source": "arbeitnow",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": job.get("candidate_required_location"),
        "url": job.get("url"),
        "posted_at": datetime.fromtimestamp(job["created_at"]).isoformat()
                           if isinstance(job.get("created_at"), (int, float))
                           else job.get("created_at"),
    }


def normalize_arbeitnow_list(rows: list[dict]) -> list[Job]:
    return [normalize_arbeitnow(j) for j in rows]
