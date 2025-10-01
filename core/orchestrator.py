from adapters import fetch_arbeitnow, fetch_agentur, fetch_remotive, get_params_agentur, get_params_remotive, get_params_arbeitnow


# ADAPTER AUFRUFEN + ERGEBNISSE SAMMELN  ## UNSER WORKFLOW ##
# aufrufen von orchestrator.py
# -> params_for + fetch = raw_jobs
# -> raw_jobs = fetch_jobs(params)

def load_params (comon_params: dict) ->dict[str, list]:
    # Wir holen die jeweiligen Parametern für die passenden API's 

    params_remotive = get_params_remotive(**comon_params)
    params_agentur = get_params_agentur(**comon_params)
    params_arbeitnow= get_params_arbeitnow(**comon_params)
    
    # Wir schicken die Anfragen an unseren API's und speichern die daten in raw.
    # Wir behalten die Ergebnisse getrennt für die Normalisierung.
    raw = {
        "remotive_raw" :fetch_remotive(params_remotive),
        "agentur_raw" : fetch_agentur(params_agentur),
        "arbeitnow_raw": fetch_arbeitnow(params_arbeitnow)
    }
    return raw  