import json
from datetime import datetime
import requests
import pandas as pd

agentur_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
# API-Key (für die öffentliche Jobsuche ist ein Standard-Key vorhanden)
headers = {
    "X-API-Key": "jobboerse-jobsuche"
}

# Parameter für die Suche: Beispiel -> Softwareentwickler in Berlin
params = {
    "was": "Softwareentwickler", # Suchbegriff
    "wo": "Berlin",              # Ort
    "page": 1,                   # Ergebnisseite
    "size": 10                   # Anzahl Treffer pro Seite
}

# GET-Request senden
response = requests.get(agentur_url, headers=headers, params=params)
print(response.status_code)

# User-Inputs

# get_params()

def get_params(search: str, category: str, company: str, limit: int | None = None) -> dict:
    params = {}
    if search and search.strip():
        params["was"] = search.strip()  # statt "search"
    if category and category.strip():
        params["berufsfeld"] = category.strip()  # optional, nur wenn API es unterstützt
    if company and company.strip():
        params["arbeitgeber"] = company.strip()  # optional, nur wenn API es unterstützt
    params["size"] = int(limit) if limit else 5
    params["page"] = 1
    return params
# Response

def fetch_agentur(params: dict) -> list[dict]:
    #  API aufrufen und in das Normalformat umwandeln.
    # params wird dieser als dict angegeben, und wenn mehr as ein dict gibt (ein job= ein dict), wird eine liste von dicts erstellt.
    r = requests.get(agentur_url, headers=headers, params=params, timeout=30)
    #Anfrage (request) mit api url, unsere userinput params (recherche Angaben), wartelimit (timeout=30)
    r.raise_for_status()
    # test der Verbindung. Wenn 200, funktionniert. Wird nicht angezeigt hier. braucht dafür ein print(r.raise_for_status()) 
    data = r.json()
    #speicher der daten in data Variabel als json Format
    return r.json().get("stellenangebote", [])
    # braucht ein return 
# Normalisierung

def normalize_agentur(stellenangebot: dict) -> dict:
    # Normalisierung der Suchbegriffe für ein dict. Nicht für die Dict liste !
    return {
        "id": f"agenturfuerarbeit:{stellenangebot.get('id')}",
        "source": "agenturfuerarbeit",
        "title": stellenangebot.get("beruf"),
        "company": stellenangebot.get("arbeitgeber"),
        "location": stellenangebot.get("arbeitsort"),
        "posted_at": stellenangebot.get("aktuelleVeroeffentlichungsdatum"),
        "url": stellenangebot.get("url")
    }
# Wir müssen noch die normalize_agentur einbauen, sodass sie die ganze liste normalisiert, und nicht nur das erste dict unserer Liste
def normalize_agentur_list(stellenangebote: list[dict]) -> list[dict]:
    return [normalize_agentur(j) for j in stellenangebote]
params = get_params(search, category, company, limit)
raw_jobs = fetch_agentur(params)
jobs = normalize_agentur_list(raw_jobs)
# Befehl an API mit usere Suchkriterien (params) und lassen uns die url anzeigen zu Controlling
r = requests.get(agentur_url, headers=headers, params=params, timeout=30)
r.raise_for_status()
print("Aufgerufene URL:", r.url)
"""data = r.json()
for j in data.get("jobs", [])[:5]:
    print("-----")
    print("Titel:", j.get("beruf"))
    print("Unternehmen:", j.get("arbeitgeber"))
    print("Ort:", j.get("arbeitsort"))
    print(Veroeffentlichungsdatum:" j.get("aktuelleVeroeffentlichungsdatum"))
    print("Link:", j.get("url"))
"""
# DataFrame Tabelle
jobs= normalize_agentur_list(raw_jobs)
pd.DataFrame(jobs)
# nach Spaltennamen schauen (siehe Beispieldaten):

print("Status:", r.status_code)
print("URL:", r.url)
print("Response JSON keys:", r.json().keys())
print("Beispieldaten:", r.json())
