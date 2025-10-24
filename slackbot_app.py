#!/usr/bin/env python3
# coding: utf-8
"""
Slack Slash Command App für /jobs
Voraussetzungen:
  - Pakete: slack-bolt, slack-sdk, flask, psycopg2-binary, python-dotenv (optional)
  - ENV Variablen:
      SLACK_SIGNING_SECRET=...
      SLACK_BOT_TOKEN=xoxb-...
      DATABASE_URL=postgres://... (Neon)
  - Slack App Config:
      Slash Command: /jobs  ->  https://<host>/slack/events   (oder /slack/commands, beide Routen sind vorhanden)
"""

import os, sys
sys.path.append(os.path.dirname(__file__))
import logging
from typing import List, Optional

from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Optional: .env laden (lokal hilfreich)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Eigene Module
from core.db_conn import get_conn  # <- NEON Verbindung

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slackbot.jobs")

# -------------------------------------------------------------------
# Slack App initialisieren (Bolt)
# -------------------------------------------------------------------
bolt_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

# Flask App für HTTP Empfang
flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

# -------------------------------------------------------------------
# Hilfsfunktionen: Query-Parsing & DB-Lesen
# -------------------------------------------------------------------

def _split_text(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Einfache Heuristik:
      - 2+ Wörter: erstes = location, rest = search
      - 1 Wort   : search
      - sonst    : nichts
    """
    parts = (text or "").strip().split()
    if not parts:
        return None, None
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], " ".join(parts[1:])

def fetch_jobs_from_db(search: Optional[str], location: Optional[str], limit: int = 10) -> list[tuple]:
    """
    Liest die letzten Jobs aus Neon.
    Filter:
      - search   -> ILIKE über title/company/location
      - location -> zusätzliches ILIKE auf location
    """
    conn = get_conn()
    cur = conn.cursor()
    if search and location:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            WHERE (title ILIKE %s OR company ILIKE %s OR location ILIKE %s)
              AND (location ILIKE %s)
            ORDER BY id DESC
            LIMIT %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{location}%", limit))
    elif search:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            WHERE title ILIKE %s OR company ILIKE %s OR location ILIKE %s
            ORDER BY id DESC
            LIMIT %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%", limit))
    elif location:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            WHERE location ILIKE %s
            ORDER BY id DESC
            LIMIT %s
        """, (f"%{location}%", limit))
    else:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            ORDER BY id DESC
            LIMIT %s
        """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def format_jobs_blocks(rows: list[tuple]) -> List[dict]:
    """
    Slack Blocks kompakt. rows: (source,title,company,location,job_type,posted_at,url)
    """
    blocks: List[dict] = []
    if not rows:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "Keine Ergebnisse gefunden."}})
        return blocks

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*{len(rows)} Treffer gefunden*  (zeige bis zu 10)"}})
    blocks.append({"type": "divider"})

    for r in rows[:10]:
        source, title, company, location, job_type, posted_at, url = r
        title = title or "(ohne Titel)"
        company = company or "(ohne Firma)"
        location = location or "(ohne Ort)"
        mode = job_type or ""
        line = f"*{title}*  bei *{company}*  {f'[{mode}]' if mode else ''}\n{location}  ·  Quelle: {source}"
        if url:
            line += f"\n<{url}|Zur Stelle>"

        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": line}})
        blocks.append({"type": "divider"})
    return blocks

# -------------------------------------------------------------------
# Slash Command: /jobs
# -------------------------------------------------------------------
@bolt_app.command("/jobs")
def cmd_jobs(ack, respond, command):
    """
    /jobs [location] [search...]
    Beispiele:
      /jobs berlin analyst
      /jobs analyst
      /jobs berlin
    """
    try:
        ack()  # schnelle Bestätigung < 3s
        text = command.get("text") or ""
        location, search = _split_text(text)
        rows = fetch_jobs_from_db(search=search, location=location, limit=10)
        blocks = format_jobs_blocks(rows)
        respond(blocks=blocks)
    except Exception as e:
        logger.exception("Fehler im /jobs Handler")
        respond(text=f"Fehler beim Laden der Jobs: {e}")

# -------------------------------------------------------------------
# HTTP-Routen (Slack & Health)
# -------------------------------------------------------------------
@flask_app.get("/health")
def health():
    return jsonify({"ok": True})

# Beide Routen unterstützen (je nach Slack-Konfiguration)
@flask_app.post("/slack/events")
def slack_events():
    return handler.handle(request)

@flask_app.post("/slack/commands")
def slack_commands():
    return handler.handle(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starte Slack HTTP Server auf Port {port}")
    flask_app.run(host="0.0.0.0", port=port)
