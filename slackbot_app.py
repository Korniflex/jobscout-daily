
#!/usr/bin/env python3
# coding: utf-8
"""
Slack Slash Command App fuer /jobs
Voraussetzungen:
  - Pakete: slack-bolt, slack-sdk, flask, pydantic, requests, python-dotenv
  - Umgebungsvariablen:
      SLACK_SIGNING_SECRET=...
      SLACK_BOT_TOKEN=xoxb-...
  - Slack App Config:
      Slash Command: /jobs  ->  https://<host>/slack/commands
"""

import os
import logging
from typing import List, Optional

from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Optional: .env laden, falls vorhanden
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Eigene Module
from core.schema import CommonQuery
from core.orchestrator import load_params
from core.normalizer import normalize_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slackbot.jobs")

# Slack App initialisieren
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

# Flask App fuer HTTP Empfang
flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)

# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------

def _split_text(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Einfache Heuristik fuer den Slash-Text:
      - Erstes Wort = location (nur falls mindestens 2 Woerter vorhanden sind)
      - Rest        = search
      Beispiele:
        "berlin analyst" -> ("berlin", "analyst")
        "analyst"        -> (None, "analyst")
        ""               -> (None, None)
    """
    parts = (text or "").strip().split()
    if not parts:
        return None, None
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], " ".join(parts[1:])

def parse_text_to_common_query(text: str) -> CommonQuery:
    """
    Erzeugt IMMER ein CommonQuery-Objekt (kein dict), um Punktzugriffe sicher zu machen.
    """
    location, search = _split_text(text)

    # Nur erlaubte Felder an CommonQuery uebergeben
    cq = CommonQuery(
        search=search or None,
        location=location or None,
        category="IT",
        limit=25,
    )
    return cq

def format_jobs_blocks(jobs) -> List[dict]:
    """
    Slack Blocks fuer eine kompakte Ausgabe erzeugen.
    Zeigt max. 10 Eintraege.
    """
    max_rows = 10
    blocks: List[dict] = []
    if not jobs:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Keine Ergebnisse gefunden."}
        })
        return blocks

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{len(jobs)} Treffer gefunden*  (zeige bis zu {max_rows})"}
    })
    blocks.append({"type": "divider"})

    for j in jobs[:max_rows]:
        title = j.title or "(ohne Titel)"
        company = j.company or "(ohne Firma)"
        location = j.location or "(ohne Ort)"
        source = j.source or ""
        url = str(j.url) if getattr(j, "url", None) else None
        mode = j.job_type or j.remote or ""
        line = f"*{title}*  bei *{company}*  {f'[{mode}]' if mode else ''}\n{location}  ·  Quelle: {source}"
        if url:
            line += f"\n<{url}|Zur Stelle>"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": line}
        })
        blocks.append({"type": "divider"})

    return blocks

# ------------------------------------------------------------
# Slash Command
# ------------------------------------------------------------

@slack_app.command("/jobs")
def handle_jobs(ack, respond, command, logger):
    """
    Slash Command Handler fuer /jobs
    Beispiel: /jobs berlin analyst
    """
    try:
        ack()  # Sofort bestaetigen

        text = command.get("text") or ""
        cq = parse_text_to_common_query(text)   # IMMER CommonQuery, kein dict

        # Daten abrufen und normalisieren
        raw = load_params(cq)               # robust gegen CommonQuery/dict
        jobs = normalize_jobs(raw)          # Liste[Job]

        blocks = format_jobs_blocks(jobs)
        respond(blocks=blocks)

    except Exception as e:
        logger.exception("Fehler im /jobs Handler")
        respond(text=f"Fehler beim Laden der Jobs: {e}")

# ------------------------------------------------------------
# Routen
# ------------------------------------------------------------

@flask_app.get("/health")
def health():
    return jsonify({"ok": True})

@flask_app.post("/slack/commands")
def slack_commands():
    return handler.handle(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starte Slack HTTP Server auf Port {port}")
    flask_app.run(host="0.0.0.0", port=port)
