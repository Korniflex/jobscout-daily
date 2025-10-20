# adapters/API_jobicy.py
import json
import requests
from datetime import datetime
from core.schema import Job

jobicy_url = "https://jobicy.com/api/v2/remote-jobs"


def get_params_jobicy(
        search: str = "",
        category: str = "",
        company: str = "",
        location: str = "",
        remote: str = "",
        work_mode: str = "",
        posted_since: str = "",
        limit: int = "",
        page: int = "",
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


def fetch_jobicy(params: dict) -> list[dict]:
 
    try:
        r = requests.get(jobicy_url, timeout=30)
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


def normalize_jobicy(job: dict) -> Job:
   
    return {
        "id": f"jobicy:{job.get('id') or job.get('jobSlug')}",
        "source": "jobicy",
        "title": job.get("jobTitle"),
        "company": job.get("companyName"),
        "location": job.get("jobGeo"),
        "url": job.get("url"),
        # pubDate у Jobicy рядок ISO — передаємо як є; за бажанням можна розпарсити:
        "posted_at": job.get("pubDate"),
    }


def normalize_jobicy_list(rows: list[dict]) -> list[Job]:
    return [normalize_jobicy(j) for j in rows]



