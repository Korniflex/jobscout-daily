
# param_translators.py
# =====================
# Zentrale Übersetzungsfunktionen: CommonQuery -> Adapter-Parameter
# Ziel: Orchestrator bleibt schlank; API-spezifische Param-Logik ist hier zentral,
# ohne das schema oder die Adapter-Funktionen zu vermischen.
#
# Integration (kurz):
#   from param_translators import to_remotive, to_agentur, to_arbeitnow, to_jobicy
#   params_remotive  = to_remotive(cq)
#   params_agentur   = to_agentur(cq)
#   params_arbeitnow = to_arbeitnow(cq)
#   params_jobicy    = to_jobicy(cq)
#   # Danach wie gewohnt:
#   # get_params_remotive(**params_remotive)  usw.
#
# WICHTIG: Die Keys, die wir hier zurückgeben, entsprechen den Signaturen Eurer
#          bestehenden get_params_* Funktionen in den Adaptern (nicht unbedingt
#          den echten API-Parametern). So muss an den Adaptern nichts geändert werden.
#
# Projekt-Konvention: Kommentare & Bezeichner auf Deutsch.

from __future__ import annotations
from typing import Dict, Any
try:
    # Pfad je nach Projektstruktur anpassen
    from core.schema import CommonQuery
except Exception:
    # Fallback, falls der Import-Pfad anders ist
    from schema import CommonQuery


# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------
def _is_blank(v: Any) -> bool:
    """True, wenn Wert None ist oder (bei Strings) nur aus Leerzeichen besteht."""
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return False

def _clean_params(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entfernt None/leere Strings und trimmt Strings.
    Behält 0/False bewusst bei.
    """
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, str):
            v = v.strip()
            if not v:
                continue
        if v is None:
            continue
        out[k] = v
    return out


# ------------------------------------------------------------
# Übersetzer pro Adapter (CommonQuery -> get_params_* Argumente)
# ------------------------------------------------------------

def to_remotive(cq: CommonQuery) -> Dict[str, Any]:
    """
    Gibt Argumente passend zu get_params_remotive(...)
    Unterstützt in Eurem Adapter:
      search, category, company, location, posted_since, work_mode, remote, limit, page
    """
    raw = {
        "search":       cq.search,
        "category":     cq.category,
        "company":      cq.company,
        "location":     cq.location,
        "posted_since": cq.posted_since,
        "work_mode":    cq.work_mode,
        "remote":       getattr(cq, "remote", None),
        "limit":        getattr(cq, "limit", None),
        "page":         getattr(cq, "page", None),
    }
    return _clean_params(raw)


def to_arbeitnow(cq: CommonQuery) -> Dict[str, Any]:
    """
    Gibt Argumente passend zu get_params_arbeitnow(...)
    Unterstützt in Eurem Adapter:
      search, category, company, location, posted_since, work_mode, remote, page, limit
    """
    raw = {
        "search":       cq.search,
        "category":     cq.category,
        "company":      cq.company,
        "location":     cq.location,
        "posted_since": cq.posted_since,
        "work_mode":    cq.work_mode,
        "remote":       getattr(cq, "remote", None),
        "page":         getattr(cq, "page", None),
        "limit":        getattr(cq, "limit", None),
    }
    return _clean_params(raw)


'''def to_agentur(cq: CommonQuery) -> Dict[str, Any]:
    """
    Gibt Argumente passend zu get_params_agentur(...)
    Unterstützt in Eurem Adapter:
      search, category, company, location, posted_since, work_mode, limit, page
    """
    raw = {
        "search":       cq.search,
        "category":     cq.category,
        "company":      cq.company,
        "location":     cq.location,
        "posted_since": cq.posted_since,
        "work_mode":    cq.work_mode,
        "limit":        getattr(cq, "limit", None),
        "page":         getattr(cq, "page", None),
    }
    return _clean_params(raw)'''


def to_jobicy(cq: CommonQuery) -> Dict[str, Any]:
    """
    Gibt Argumente passend zu get_params_jobicy(...)
    Unterstützt in Eurem Adapter:
      search, category, company, location, remote, work_mode, posted_since, limit, page
    Hinweis: Euer fetch_jobicy() nutzt momentan keine Query-Params,
             aber diese Übersetzung bleibt zukunftssicher.
    """
    raw = {
        "search":       cq.search,
        "category":     cq.category,
        "company":      cq.company,
        "location":     cq.location,
        "remote":       getattr(cq, "remote", None),
        "work_mode":    cq.work_mode,
        "posted_since": cq.posted_since,
        "limit":        getattr(cq, "limit", None),
        "page":         getattr(cq, "page", None),
    }
    return _clean_params(raw)
