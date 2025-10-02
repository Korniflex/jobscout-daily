import json
import requests
from core.schema import Job


remotive_url = "https://remotive.com/api/remote-jobs"

def get_params_remotive(search: str = "", 
               category: str = "", 
               company: str = "", 
               location: str="") -> dict:
    params :dict= {}
    if search and search.strip():
        params["search"] = search.strip()
    if category and category.strip():
        params["category"] = category.strip()
    if company and company.strip():
        params["company_name"] = company.strip()
    if location and location.strip():
        params["candidate_required_location"] = location.strip()
    return params

def fetch_remotive(params: dict) -> list[dict]:
    r = requests.get(remotive_url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("jobs", [])

def normalize_remotive(job: dict) -> Job:
    return {
        "id": f"remotive:{job.get('id')}",
        "source": "remotive",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": job.get("candidate_required_location"),
        "url": job.get("url"),
        "posted_at": job.get("publication_date"),
    }

def normalize_remotive_list(rows: list[dict]) -> list[Job]:
    return [normalize_remotive(j) for j in rows]