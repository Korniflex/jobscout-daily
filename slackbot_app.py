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
import json
import re
sys.path.append(os.path.dirname(__file__))
import logging
from typing import List, Optional

from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from asgiref.wsgi import WsgiToAsgi

# Optional: .env laden (lokal hilfreich)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- ASGI-Wrapper für Flask, damit Uvicorn es starten kann ---


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
asgi_app = WsgiToAsgi(flask_app)
handler = SlackRequestHandler(bolt_app)

# -------------------------------------------------------------------
# Hilfsfunktionen: Query-Parsing & DB-Lesen
# -------------------------------------------------------------------

def _split_text(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse Slash Command Text mit Support für Quotes.
    
    Unterstützte Formate:
      /jobs "data analyst"           -> location=None, search="data analyst"
      /jobs berlin "data analyst"    -> location="berlin", search="data analyst"
      /jobs "data analyst" berlin    -> location="berlin", search="data analyst"
      /jobs berlin analyst           -> location="berlin", search="analyst"
      /jobs analyst                  -> location=None, search="analyst"
    
    Returns:
      (location, search)
    """
    text = (text or "").strip()
    if not text:
        return None, None
    
    # Suche nach Text in Quotes (sowohl " als auch ')
    quote_pattern = r'["\']([^"\']+)["\']'
    quote_match = re.search(quote_pattern, text)
    
    if quote_match:
        # Text in Quotes ist der Suchbegriff
        search = quote_match.group(1).strip()
        
        # Rest (ohne Quotes) ist der Standort
        location_text = re.sub(quote_pattern, '', text).strip()
        location = location_text if location_text else None
        
        logger.info(f"Parsed with quotes: location='{location}', search='{search}'")
        return location, search
    
    # Keine Quotes: alte Logik
    parts = text.split()
    if len(parts) == 1:
        logger.info(f"Parsed single word: location=None, search='{parts[0]}'")
        return None, parts[0]
    
    # 2+ Wörter: erstes = location, rest = search
    location = parts[0]
    search = " ".join(parts[1:])
    logger.info(f"Parsed multiple words: location='{location}', search='{search}'")
    return location, search

    if len(parts) == 1:
        return None, parts[0]
    return parts[0], " ".join(parts[1:])

def fetch_jobs_from_db(search: Optional[str], location: Optional[str], limit: int = 10, offset: int = 0) -> list[tuple]:
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
            OFFSET %s         
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{location}%", limit, offset))
    elif search:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            WHERE title ILIKE %s OR company ILIKE %s OR location ILIKE %s
            ORDER BY id DESC
            LIMIT %s
            OFFSET %s         
        """, (f"%{search}%", f"%{search}%", f"%{search}%", limit, offset))
    elif location:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            WHERE location ILIKE %s
            ORDER BY id DESC
            LIMIT %s
            OFFSET %s        
        """, (f"%{location}%", limit, offset))
    else:
        cur.execute("""
            SELECT source,title,company,location,job_type,posted_at,url
            FROM jobs
            ORDER BY id DESC
            LIMIT %s
            OFFSET %s        
        """, (limit, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def format_jobs_blocks(rows: list[tuple], search_term: str = None, location_filter : str =None, offset: int = 0) -> List[dict]:
    """
    Slack Blocks kompakt. 
    rows: (source,title,company,location,job_type,posted_at,url)

    Renamed parameters to avoid confusion:
      - search_term: the search query
      - location_filter: the location filter
    """
    blocks: List[dict] = []
    if not rows:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "Keine Ergebnisse gefunden."}})
        return blocks

    # Header
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*{len(rows)} Treffer gefunden*  (zeige bis zu 10)"}})
    blocks.append({"type": "divider"})

    #Jobs anzeigen
    for r in rows[:10]:
        source, title, company, job_location, job_type, posted_at, url = r
        title = title or "(ohne Titel)"
        company = company or "(ohne Firma)"
        job_location = job_location or "(ohne Ort)"
        mode = job_type or ""
        line = f"*{title}*  bei *{company}*  {f'[{mode}]' if mode else ''}\n{job_location}  ·  Quelle: {source}"
        if url:
            line += f"\n<{url}|Zur Stelle>"

        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": line}})
        blocks.append({"type": "divider"})


    button_value = json.dumps({
            "search": search_term or "",
            "location": location_filter or "",
            "offset": offset + 10
        })

    blocks.append({
            "type": "actions",
            "elements": [
                {

                    "type":"button",
                    "text": {"type": "plain_text", "text": "Mehr anzeigen"},
                    "action_id": "show_more_jobs",
                    "value": button_value
                }
            ]
        })
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
        ack() # schnelle Bestätigung < 3s
        text = command.get("text") or ""
        logger.info(f"User Suchkriterie : /jobs {text}")

        location, search = _split_text(text)
        logger.info(f"Konvertierte User Eingabe: location = '{location}', search= '{search}'")

        rows = fetch_jobs_from_db(search_term=search, location_filter =location, limit=10)
        blocks = format_jobs_blocks(rows)
        respond(blocks=blocks)  
    except Exception as e:
        logger.exception("Fehler im /jobs Handler")
        respond(text=f"Fehler beim Laden der Jobs: {e}")



#-------------------------------------------------------------------
# Button Befehl (mehr anzeigen)
#-------------------------------------------------------------------
@bolt_app.action("show_more_jobs")
def handle_show_more(ack, body, respond):
    """
    Handler fuer den Show More Button
    """

    try:
        ack()

        #parse vutton value
        button_value= json.loads(body["actions"][0]["value"])
        search = button_value.get("search") or None
        location = button_value.get("location") or None
        offset = button_value.get("offset", 10)

        logger.info(f"Mehr anzeigen: search='{search}', location='{location}', offset={offset}")

        #Laden von weiteren Jobs
        rows = fetch_jobs_from_db(search= search, location= location, limit=10, offset= offset)

        if not rows:
            respond(
                text= "Keine weiteren Jobs gefunden.",
                replace_original = False
            )
            return
        
        #Erstellt neue Blocks
        blocks= format_jobs_blocks(rows, search_term= search, location_filter= location, offset= offset)

        #Fuege neue Jobs hinxu (nicht ersetzen)
        respond(
            blocks=blocks,
            replace_original= False
        )

    except Exception as e:
        logger.exception("fehler im Mehr anzeigen Handler")
        respond(
            text="Fehler beim Laden weiterer Jobs: {e}"
        )





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
