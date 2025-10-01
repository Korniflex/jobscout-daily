import json
from datetime import datetime
import requests
import pandas as pd

agentur_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
# API-Key (für die öffentliche Jobsuche ist ein Standard-Key vorhanden)
headers = {
    "X-API-Key": "jobboerse-jobsuche"
}

def get_params_agentur(search: str = "", 
               category: str = "", 
               company: str = "", 
               location: str="") -> dict:
    """Baut die Parameter für die Bundesagentur-API basierend auf Benutzereingaben."""
    params: dict = {}
    if search and search.strip():
        params["was"] = search.strip()
    if category and category.strip():
        params["berufsfeld"] = category.strip()
    if company and company.strip():
        params["arbeitgeber"] = company.strip()
    if location and location.strip():
        params["arbeitsorte"]= location.strip()
    params["page"] = 1
    
    return params
# Response

def fetch_agentur(params: dict) -> list[dict]:
    """Ruft die Bundesagentur-API auf und gibt die rohe Liste von Stellenangeboten zurück."""
    r = requests.get(agentur_url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("stellenangebote", [])

def _extract_location(sa: dict):
    loc = sa.get("arbeitsort")
    if isinstance(loc, dict):
        for k in ("ort", "plz", "region", "land"):
            if k in loc and loc[k]:
                return str(loc[k])
        return json.dumps(loc, ensure_ascii=False)
    return loc

def normalize_agentur(job: dict) -> dict:
    # Normalisierung der Suchbegriffe für ein dict. Nicht für die Dict liste !
    return {
        "id": f"agenturfuerarbeit:{job.get('id')}",
        "source": "agenturfuerarbeit",
        "title": job.get("beruf"),
        "company": job.get("arbeitgeber"),
        "location": _extract_location(job),
        "posted_at": job.get("aktuelleVeroeffentlichungsdatum"),
        "url": job.get("url")
    }
# Wir müssen noch die normalize_agentur einbauen, sodass sie die ganze liste normalisiert, und nicht nur das erste dict unserer Liste
def normalize_agentur_list(rows: list[dict]) -> list[dict]:
    return [normalize_agentur(j) for j in rows]


