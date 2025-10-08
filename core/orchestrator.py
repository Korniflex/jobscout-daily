
from schema import CommonQuery
from adapters import (
    get_params_remotive, get_params_agentur, get_params_arbeitnow,
    fetch_remotive, fetch_agentur, fetch_arbeitnow,
)

def load_params(cq: CommonQuery) -> dict[str, list]:
    # Wir holen die jeweiligen Parametern für die passenden APIs
    try:
        cq_map = cq.model_dump()   # Pydantic v2
    except AttributeError:
        cq_map = cq.dict()         # Pydantic v1 (ich habe ein envirement Problem und musste hier meine Versaion von pydantic erstellen

    params_remotive  = get_params_remotive(**cq_map)
    params_agentur   = get_params_agentur(**cq_map)
    params_arbeitnow = get_params_arbeitnow(**cq_map)

    # Wir schicken die Anfragen an unsere APIs und speichern die Daten in raw.
    # Wir behalten die Ergebnisse getrennt für die Normalisierung.
    raw = {
        "remotive_raw":  fetch_remotive(params_remotive),
        "agentur_raw":   fetch_agentur(params_agentur),
        "arbeitnow_raw": fetch_arbeitnow(params_arbeitnow),
    }
    return raw