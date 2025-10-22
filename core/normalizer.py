
# Wir wollen die Ergebnisse von load_params() die in raw_jobs sind, normalisieren.
# Hier weiß ich nicht ob die Funktionen Sinn machen. 
from adapters import normalize_agentur_list, normalize_arbeitnow_list, normalize_remotive_list,normalize_jobicy_list
from typing import Any
from core.schema import Job

def _coerce_listlike_to_str(v: Any) -> str | None:

    """
    Wandelt Listen oder Dictionaries in einen String um.
    Beispiel:
      ['Full-Time', 'Remote'] -> "Full-Time, Remote"
      {'type': 'Full-Time'}  -> "type:Full-Time"
    """
    if v is None:
        return None
    if isinstance(v, list):
        return ", ".join(map(str, v))
    if isinstance(v, dict):
        return ", ".join(f"{k}:{val}" for k, val in v.items())
    return str(v)

def _preprocess_row(row: dict) -> dict:
    """
    Vorverarbeitung von Rohdaten (API → Job).
    Ziel:
      - Einheitliches Feld "job_type"
      - Sicherstellen, dass der Wert ein String ist, selbst wenn die API eine Liste liefert.
    """
    out = dict(row)  # flache Kopie

    # Häufige Varianten der Feldnamen zwischen APIs
    job_type_keys = (
        "job_type",
        "jobType",
        "job_types",
        "employment_type",
        "employmentTypes",
        "type",
        "types",
    )

    # Falls das Feld "job_type" nicht gesetzt ist, prüfen wir alternative Keys
    if "job_type" not in out or out.get("job_type") in (None, [], {}):
        for k in job_type_keys:
            if k in out and out[k] not in (None, [], {}):
                out["job_type"] = out[k]
                break

    # Endgültige Umwandlung in String
    if "job_type" in out:
        out["job_type"] = _coerce_listlike_to_str(out["job_type"])

    return out

def normalize_jobs(all_raw_jobs: dict) -> list[Job]:
    rows: list[dict] = []

    if all_raw_jobs.get("remotive_raw"):
        rows += normalize_remotive_list(all_raw_jobs["remotive_raw"])

    #if all_raw_jobs.get("agentur_raw"):
    #   rows += normalize_agentur_list(all_raw_jobs["agentur_raw"])

    if all_raw_jobs.get("arbeitnow_raw"):
        rows += normalize_arbeitnow_list(all_raw_jobs["arbeitnow_raw"])

    if all_raw_jobs.get("jobicy_raw"):
        rows += normalize_jobicy_list(all_raw_jobs["jobicy_raw"])

    jobs: list[Job] = []
    for i, r in enumerate(rows):
        try:
            r = _preprocess_row(r)
            jobs.append(Job(**r))
        except Exception as e:
            print("Überspringe ungültige Zeile", i, e)

    return jobs
