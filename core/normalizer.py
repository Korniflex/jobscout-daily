from adapters import normalize_agentur, normalize_arbeitnow, normalize_remotive,normalize_arbeitnow_list, normalize_agentur_list, normalize_remotive_list

# Wir wollen die Ergebnisse von load_params() die in raw_jobs sind, normalisieren.
# Hier weiß ich nicht ob die Funktionen Sinn machen. 
def normalize_jobs(all_raw_jobs:dict) ->list [dict]:
    normalized_jobs: list[dict]= []

    # Remotive
    if all_raw_jobs.get("remotive_raw"):
        normalized_jobs += normalize_remotive_list(all_raw_jobs["remotive_raw"])

    # Bundenagentur
    if all_raw_jobs.get("agentur_raw"):
        normalized_jobs += normalize_agentur_list(all_raw_jobs["agentur_raw"])

    # Arbeitnow
    if all_raw_jobs.get("arbeitnow_raw"):
        normalized_jobs += normalize_arbeitnow_list(all_raw_jobs["arbeitnow_raw"])

    return normalized_jobs