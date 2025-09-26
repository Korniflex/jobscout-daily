import requests

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"

def get_params(search: str = "", category: str = "", company: str = "", limit: int = 10) -> dict:
    params :dict= {}
    if search and search.strip():
        p["search"] = search.strip()
    if category and category.strip():
        p["category"] = category.strip()
    if company and company.strip():
        p["company_name"] = company.strip()
    if isinstance(limit, int) and limit > 0:
        p["limit"] = limit
    return params

def fetch_remotive(params: dict) -> list[dict]:
    r = requests.get(REMOTIVE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("jobs", [])

def normalize_remotive(job: dict) -> dict:
    return {
        "id": f"remotive:{job.get('id')}",
        "source": "remotive",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": job.get("candidate_required_location"),
        "url": job.get("url"),
        "posted_at": job.get("publication_date"),
    }

def normalize_remotive_list(rows: list[dict]) -> list[dict]:
    return [normalize_remotive(j) for j in rows]