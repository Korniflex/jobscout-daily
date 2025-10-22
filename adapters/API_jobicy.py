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
        api_params = {}
        if 'limit' in params:
            api_params['count'] = params['limit']
        
        r = requests.get(jobicy_url, params=api_params, timeout=30)
        r.raise_for_status()
        data = r.json()
        jobs = data.get("jobs", [])
        
        # Lokale Filterung nach category/search
        if params.get('category') or params.get('search'):
            jobs = [j for j in jobs if _matches_filters(j, params)]
        
        print(f"  Jobicy_raw: {len(jobs)} jobs gefunden")
        return jobs
    except Exception as e:
        print(f"Error Jobicy: {e}")
        return []

def _matches_filters(job: dict, params: dict) -> bool:
    """Lokale Filterung da API keine Parameter unterstützt"""
    category = params.get('category', '').lower()
    search = params.get('search', '').lower()
    
    # Wenn weder category noch search gesetzt sind, alle Jobs durchlassen
    if not category and not search:
        return True
    
    if category:
        # Probiere verschiedene Felder für Kategorie
        job_industry = str(job.get('jobIndustry', '')).lower()
        job_category = str(job.get('category', '')).lower()
        job_title = str(job.get('jobTitle', '')).lower()
        
        # Suche in allen relevanten Feldern
        if category in job_industry or category in job_category or category in job_title:
            return True
        
        # Wenn category="IT" ist, suche auch nach "software", "developer", etc.
        if category == 'it':
            it_keywords = ['software', 'developer', 'engineer', 'programming', 'tech', 'data', 'it ']
            if any(kw in job_title or kw in job_industry for kw in it_keywords):
                return True
        
        return False
    
    if search:
        searchable = f"{job.get('jobTitle', '')} {job.get('companyName', '')} {job.get('jobIndustry', '')}".lower()
        if search not in searchable:
            return False
    
    return True


def normalize_jobicy(job: dict) -> Job:
   
    return {
        "id": f"jobicy:{job.get('id') or job.get('jobSlug')}",
        "source": "jobicy",
        "title": job.get("jobTitle"),
        "job_type" : job.get("jobType"),
        "company": job.get("companyName"),
        "location": job.get("jobGeo"),
        "url": job.get("url"),
        # pubDate у Jobicy рядок ISO — передаємо як є; за бажанням можна розпарсити:
        "posted_at": job.get("pubDate"),
    }


def normalize_jobicy_list(rows: list[dict]) -> list[Job]:
    return [normalize_jobicy(j) for j in rows]



