from adapters import normalize_agentur, normalize_arbeitnow, normalize_remotive,normalize_arbeitnow_list, normalize_agentur_list, normalize_remotive_list
from core.schema import Job # Einsetzung der Klasse

# Wir wollen die Ergebnisse von load_params() die in raw_jobs sind, normalisieren.
# Hier weiß ich nicht ob die Funktionen Sinn machen. 
from adapters import normalize_agentur_list, normalize_arbeitnow_list, normalize_remotive_list
from core.schema import Job

def normalize_jobs(all_raw_jobs: dict) -> list[Job]:
    rows: list[dict] = []

    if all_raw_jobs.get("remotive_raw"):
        rows += normalize_remotive_list(all_raw_jobs["remotive_raw"])

    if all_raw_jobs.get("agentur_raw"):
        rows += normalize_agentur_list(all_raw_jobs["agentur_raw"])

    if all_raw_jobs.get("arbeitnow_raw"):
        rows += normalize_arbeitnow_list(all_raw_jobs["arbeitnow_raw"])

    jobs: list[Job] = []
    for i, r in enumerate(rows):
        try:
            jobs.append(Job(**r))
        except Exception as e:
            
            print("Skip invalid row", i, e)

    return jobs
