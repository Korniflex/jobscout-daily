import requests
import pandas as pd
from pandas import json_normalize
from datetime import datetime


arbeitnow_url = 'https://www.arbeitnow.com/api/job-board-api'


def get_params(search: str = "", 
               category: str = "", 
               company: str = "",  
               location: str=""
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
    return params

def fetch_arbeitnow(params: dict) -> list[dict]:
    r = requests.get(arbeitnow_url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json() or {}
    jobs = data.get("data") or data.get("jobs")
    return jobs if isinstance(jobs, list) else []


def normalize_arbeitnow(job: dict) -> dict:
    return {
        "id": f"arbeitnow:{job.get('id')or job.get('slug')}",
        "source": "arbeitnow",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": job.get("candidate_required_location"),
        "url": job.get("url"),
        "posted_at": job.get("created_at"),
    }


def normalize_arbeitnow_list(rows: list[dict]) -> list[dict]:
    return [normalize_arbeitnow(j) for j in rows]
