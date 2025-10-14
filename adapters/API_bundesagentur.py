# adapters/API_bundesagentur.py
# Nutzt jobsuche.api.bund.dev - Community Wrapper ohne Auth

import requests
from typing import Optional, List
from core.schema import Job

# Community API Endpoint (kein Auth noetig)
JOBS_URL = "https://jobsuche.api.bund.dev/pc/v1/jobs"


def get_params_agentur(
    search: str = "",
    category: str = "",
    company: str = "",
    location: str = "",
    posted_since: str = "",
    work_mode: str = "",
    remote: str = "",
    page: int = 1,
    limit: int = 25,
    **kwargs
) -> dict:
    """
    Bereitet Parameter fuer Bundesagentur API vor.
    """
    params = {}
    
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
        params["limit"] = limit
        
    return params


def fetch_agentur(params: dict) -> list[dict]:
    """
    Holt Jobs von Bundesagentur API via Community Wrapper.
    Kein Authentication noetig.
    """
    headers = {
        "User-Agent": "JobScout/1.0",
        "Accept": "application/json"
    }
    
    # API Parameter aufbauen
    page_num = max(1, int(params.get("page", 1)))  # 1-basiert bei diesem Endpoint
    size = max(1, min(100, int(params.get("limit", 25))))
    
    # 'was' Parameter - nutze category oder search
    was = (params.get("category") or params.get("search") or "").strip()
    if not was:
        was = "IT"  # Fallback
    
    api_params = {
        "page": page_num,
        "size": size,
        "was": was
    }
    
    # Optional: wo (Standort)
    wo = (params.get("location") or "").strip()
    if wo:
        api_params["wo"] = wo
    
    try:
        r = requests.get(JOBS_URL, headers=headers, params=api_params, timeout=30)
        r.raise_for_status()
        data = r.json() or {}
        
        # Response Format kann variieren
        jobs = data.get("stellenangebote") or data.get("jobs") or data.get("data") or []
        
        # Lokale Filter anwenden
        jobs = _apply_filters(jobs, params)
        
        print(f"  agentur_raw: {len(jobs)} jobs gefunden")
        if jobs:
            print(f"    Beispiel: {jobs[0].get('beruf') or jobs[0].get('title')}")
        
        return jobs
        
    except requests.HTTPError as e:
        status = e.response.status_code
        text = e.response.text[:300]
        print(f"Agentur HTTP-Fehler {status}: {text}")
        
        # Fallback: Gebe leere Liste zurueck statt Fehler
        print("  agentur_raw: 0 jobs gefunden (API nicht verfuegbar)")
        return []
        
    except Exception as e:
        print(f"Agentur Fehler: {e}")
        print("  agentur_raw: 0 jobs gefunden")
        return []


def _apply_filters(jobs: list[dict], params: dict) -> list[dict]:
    """
    Wendet lokale Filter an.
    """
    search = str(params.get("search") or "").lower().strip()
    company = str(params.get("company_name") or "").lower().strip()
    location = str(params.get("location") or "").lower().strip()
    
    if not search and not company and not location:
        return jobs
    
    filtered = []
    for job in jobs:
        title = str(job.get("beruf") or job.get("title") or "").lower()
        comp = str(job.get("arbeitgeber") or job.get("company") or "").lower()
        loc = _extract_location(job) or ""
        loc_lower = str(loc).lower()
        
        # Filter: search
        if search and search not in f"{title} {comp} {loc_lower}":
            continue
        
        # Filter: company
        if company and company not in comp:
            continue
        
        # Filter: location
        if location and location not in loc_lower:
            continue
        
        filtered.append(job)
    
    return filtered


def _extract_location(job: dict) -> Optional[str]:
    """
    Extrahiert Standort aus verschiedenen Formaten.
    """
    # Versuche arbeitsort
    loc = job.get("arbeitsort")
    if isinstance(loc, dict):
        for key in ("ort", "plz", "region"):
            val = loc.get(key)
            if val:
                return str(val)
    elif loc:
        return str(loc)
    
    # Fallback: location field
    loc = job.get("location")
    if loc:
        return str(loc)
    
    return None


def normalize_agentur(job: dict) -> Job:
    """
    Normalisiert Bundesagentur Job ins Job Schema.
    Handhabt verschiedene API Response Formate.
    """
    job_id = job.get("hashId") or job.get("id") or "unknown"
    
    # URL aufbauen
    if str(job_id).startswith("http"):
        url = str(job_id)
    else:
        url = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{job_id}"
    
    # Title
    title = job.get("beruf") or job.get("title")
    
    # Company
    company = job.get("arbeitgeber") or job.get("company")
    
    # Location
    location = _extract_location(job)
    
    # Remote ableiten
    remote_mode = None
    if title:
        title_lower = str(title).lower()
        if any(kw in title_lower for kw in ["remote", "homeoffice", "home office", "hybrid"]):
            remote_mode = "hybrid" if "hybrid" in title_lower else "remote"
    
    # Posted date
    posted = job.get("aktuelleVeroeffentlichungsdatum") or job.get("posted_at")
    
    return {
        "id": f"agenturfuerarbeit:{job_id}",
        "source": "agenturfuerarbeit",
        "title": title,
        "company": company,
        "location": location,
        "job_type": None,
        "remote": remote_mode,
        "url": url,
        "posted_at": posted,
    }


def normalize_agentur_list(rows: list[dict]) -> list[Job]:
    """Normalisiert Liste von Bundesagentur Jobs."""
    return [normalize_agentur(j) for j in rows]