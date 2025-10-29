#!/usr/bin/env python3
# slackbot_app.py
import os
import re
import logging
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from asgiref.wsgi import WsgiToAsgi

# DB Connection
from core.db_conn import get_conn, put_conn

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slackbot")

# ENV-Variablen prüfen
required_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "DATABASE_URL"]
for var in required_vars:
    if not os.environ.get(var):
        raise RuntimeError(f"Missing required env var: {var}")

# Slack Bolt App
bolt_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

# Flask für HTTP
flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

# ASGI Wrapper für Uvicorn
asgi_app = WsgiToAsgi(flask_app)


def parse_search(text: str) -> dict:
    """
    Parsed /jobs Kommando:
      /jobs python
      /jobs berlin python
      /jobs "data analyst" berlin remote
    """
    text = (text or "").strip().lower()
    result = {"q": None, "loc": None, "remote": False}
    
    if not text:
        return result
    
    # Remote-Flag erkennen
    if "remote" in text:
        result["remote"] = True
        text = text.replace("remote", "").strip()
    
    # Zitate berücksichtigen
    quoted = re.findall(r'"([^"]+)"', text)
    rest = re.sub(r'"[^"]+"', "", text).split()
    tokens = [*quoted, *rest]
    tokens = [t.strip() for t in tokens if t.strip()]
    
    if tokens:
        result["q"] = tokens[0]
    if len(tokens) > 1:
        result["loc"] = tokens[1]
    
    return result


def make_blocks(rows: list[tuple]) -> list[dict]:
    """Erstellt Slack Block Kit aus DB-Rows."""
    blocks = []
    
    for title, company, location, url, posted_at in rows:
        title = title or "Ohne Titel"
        company = company or "Unbekannt"
        location = location or "Remote"
        
        text = f"*{title}*\n{company} · {location}"
        if posted_at:
            text += f" · {posted_at}"
        if url:
            text += f"\n<{url}|Zur Stelle →>"
        
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        blocks.append({"type": "divider"})
    
    # Letzten Divider entfernen
    if blocks:
        blocks.pop()
    
    return blocks


@bolt_app.command("/jobs")
def handle_jobs(ack, respond, command):
    """Slash Command Handler für /jobs."""
    ack()  # Sofortige Bestätigung
    
    params = parse_search(command.get("text", ""))
    logger.info(f"/jobs called: {params}")
    
    # SQL Query aufbauen
    clauses = []
    sql_params = []
    
    if params["q"]:
        like = f"%{params['q']}%"
        clauses.append("(LOWER(title) LIKE %s OR LOWER(company) LIKE %s)")
        sql_params.extend([like, like])
    
    if params["loc"]:
        clauses.append("LOWER(COALESCE(location,'')) LIKE %s")
        sql_params.append(f"%{params['loc']}%")
    
    if params["remote"]:
        clauses.append("LOWER(COALESCE(remote,'')) = 'remote'")
    
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    
    sql = f"""
        SELECT
            title,
            company,
            location,
            url,
            to_char(posted_at::date, 'YYYY-MM-DD') AS posted_at
        FROM jobs
        {where_clause}
        ORDER BY posted_at DESC NULLS LAST
        LIMIT 10
    """
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, tuple(sql_params))
            rows = cur.fetchall()
    except Exception as e:
        logger.error(f"DB Error: {e}")
        respond("⚠️ Fehler beim Abrufen der Jobs. Bitte später versuchen.")
        return
    finally:
        put_conn(conn)
    
    if not rows:
        respond("Keine Jobs gefunden. Versuche `/jobs python`, `/jobs berlin remote` oder `/jobs \"data analyst\"`.")
        return
    
    blocks = make_blocks(rows)
    respond(blocks=blocks, text=f"{len(rows)} Jobs gefunden")


@flask_app.post("/slack/events")
def slack_events():
    """Slack Events Endpoint."""
    return handler.handle(request)


@flask_app.get("/health")
@flask_app.get("/healthz")
def health():
    """Health Check mit DB-Probe."""
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ok", "db": "connected"}, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "db": str(e)}, 500
    finally:
        put_conn(conn)


@flask_app.get("/")
def root():
    """Root Endpoint."""
    return "JobScout Slackbot - Running ✓", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starting Slackbot on port {port}")
    flask_app.run(host="0.0.0.0", port=port)