import json
from datetime import datetime
import requests
import pandas as pd

remotive_URL= "https://remotive.com/api/remote-jobs"
response= requests.get(remotive_URL)
print(response.status_code)



#Funktion um unsere Variabeln für die API verständlich zu machen
# if search = True wenn NotBLank, False wenn None oder ""
# search.strip() = entfernt die Leerzeichen am Anfang und Ende
#Die Funktion üeberprüft das die variabel nicht leer sind nachdem die Leerzeichen weggenommen wurden.
# API's mögen keine Leere Variabeln, deswegen diese Funktion

def  get_params(search: str, category : str, company :str, limit : int | None = None )-> dict:
    params = {}
    if search and search.strip():
        params["search"] = search.strip()
    if category and category.strip():
        params["category"] = category.strip()
    if company and company.strip():
        params["company_name"] = company.strip()
    if limit is not None:
        params["limit"] = int(limit)
    return params

def fetch_remotive(params: dict) -> list[dict]:
    #  API aufrufen und in das Normalformat umwandeln.
    # params wird dieser als dict angegeben, und wenn mehr as ein dict gibt (ein job= ein dict), wird eine liste von dicts erstellt.
    r = requests.get(remotive_URL, params=params, timeout=30)
    #Anfrage (request) mit api url, unsere userinput params (recherche Angaben), wartelimit (timeout=30)
    r.raise_for_status()
    # test der Verbindung. Wenn 200, funktionniert. Wird nicht angezeigt hier. braucht dafür ein print(r.raise_for_status()) 
    data = r.json()
    #speicher der daten in data Variabel als json Format
    return r.json().get("jobs", [])
    # braucht ein return 

def normalize_remotive(job: dict) -> dict:
    # Normalisierung der Suchbegriffe für ein dict. Nicht für die Dict liste !
    return {
        "id": f"remotive:{job.get('id')}",
        "source": "remotive",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": job.get("candidate_required_location"),
        "url": job.get("url"),
        "posted_at": job.get("publication_date"),
    }
# Wir müssen noch die normalize_remotive einbauen, sodass sie die ganze liste Normalisiert, und nicht nur das erste dict unserer Liste
def normalize_remotive_list(jobs: list[dict]) -> list[dict]:
    return [normalize_remotive(j) for j in jobs]

# Hier bauen wir die Funktionen  in usere Strukturlogik ein

params = get_params(search, category, company, limit)
raw_jobs = fetch_remotive(params)
jobs = normalize_remotive_list(raw_jobs)

# Befehl an der API mit usere Suchkriterien (params)  und lassen uns die url anzeigen zum Controlling
r = requests.get(remotive_URL, params=params, timeout=30)
r.raise_for_status()
print("Aufgerufene URL:", r.url)

"""data = r.json()
for j in data.get("jobs", [])[:5]:
    print("-----")
    print("Titel:", j.get("title"))
    print("Unternehmen:", j.get("company_name"))
    print("Ort:", j.get("candidate_required_location"))
    print("Link:", j.get("url"))
"""
# Wir lassen uns die r (response) in ein DF angeben
jobs= normalize_remotive_list(raw_jobs)
pd.DataFrame(jobs)