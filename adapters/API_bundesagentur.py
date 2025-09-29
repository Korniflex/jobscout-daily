import json
from datetime import datetime
import requests
import pandas as pd

agentur_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
# API-Key (für die öffentliche Jobsuche ist ein Standard-Key vorhanden)
headers = {
    "X-API-Key": "jobboerse-jobsuche"
}

def get_params(search: str = "", category: str = "", company: str = "", limit: int = 10) -> dict:
    """Baut die Parameter für die Bundesagentur-API basierend auf Benutzereingaben."""
    params: dict = {}
    if search and search.strip():
        params["was"] = search.strip()
    if category and category.strip():
        params["berufsfeld"] = category.strip()
    if company and company.strip():
        params["arbeitgeber"] = company.strip()
    params["size"] = int(limit) if isinstance(limit, int) and limit > 0 else 5
    params["page"] = 1
    return params
# Response

def fetch_agentur(params: dict) -> list[dict]:
    """Ruft die Bundesagentur-API auf und gibt die rohe Liste von Stellenangeboten zurück."""
    r = requests.get(agentur_url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("stellenangebote", [])


def normalize_agentur(job: dict) -> dict:
    # Normalisierung der Suchbegriffe für ein dict. Nicht für die Dict liste !
    return {
        "id": f"agenturfuerarbeit:{job.get('id')}",
        "source": "agenturfuerarbeit",
        "title": job.get("beruf"),
        "company": job.get("arbeitgeber"),
        "location": job.get("arbeitsort"),
        "posted_at": job.get("aktuelleVeroeffentlichungsdatum"),
        "url": job.get("url")
    }
# Wir müssen noch die normalize_agentur einbauen, sodass sie die ganze liste normalisiert, und nicht nur das erste dict unserer Liste
def normalize_agentur_list(rows: list[dict]) -> list[dict]:
    return [normalize_agentur(j) for j in rows]


""" ???
In welche Variable wird die normalisierte Liste gespeichert?
Damit wir die Variable in die main.py importieren können,
vom Modul adapters.
"""
