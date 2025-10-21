
# core/orchestrator.py
# ====================
# Zweck: Zentrale Orchestrierung der API-Adapter.
#        Nimmt CommonQuery ODER dict entgegen und liefert rohe Ergebnismengen je Quelle.
# Hinweis: Kommentare und Titel sind auf Deutsch, wie gewuenscht.

from typing import Dict, List, Union
from core.schema import CommonQuery
from adapters import (
    get_params_remotive, get_params_agentur, get_params_arbeitnow, get_params_jobicy,
    fetch_remotive, fetch_agentur, fetch_arbeitnow, fetch_jobicy,
)

# Erlaubte Schluessel aus CommonQuery/dict -> werden an die get_params_* weitergereicht
ALLOWED_KEYS = {
    "search", "category", "company", "location", "posted_since", "work_mode", "remote", "limit", "page"
}

def _to_kwargs(cq: Union[CommonQuery, Dict]) -> Dict:
    """
    Konvertiert CommonQuery/dict in ein 'kwargs'-Dict und filtert unbekannte Keys (z.B. category_synonyms).
    """
    if isinstance(cq, dict):
        d = dict(cq)  # flache Kopie
    else:
        # Pydantic v2: model_dump(); (falls v1 genutzt wuerde: cq.dict())
        d = cq.model_dump()

    # Filtere nur erlaubte Felder, unbekannte werden verworfen
    return {k: d.get(k) for k in ALLOWED_KEYS if k in d}

def load_params(cq: Union[CommonQuery, Dict]) -> Dict[str, List]:
    """
    Orchestriert die Abfragen an die einzelnen Adapter und gibt rohe Ergebnislisten zurueck.
    """
    cq_map = _to_kwargs(cq)

    params_remotive   = get_params_remotive(**cq_map)
    params_agentur    = get_params_agentur(**cq_map)
    params_arbeitnow  = get_params_arbeitnow(**cq_map)
    params_jobicy     = get_params_jobicy(**cq_map)

    raw = {
        "remotive_raw":   fetch_remotive(params_remotive),
        "agentur_raw":    fetch_agentur(params_agentur),
        "arbeitnow_raw":  fetch_arbeitnow(params_arbeitnow),
        "jobicy_raw":     fetch_jobicy(params_jobicy),
    }
    return raw
