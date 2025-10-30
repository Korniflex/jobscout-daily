#!/usr/bin/env python3
# slackbot_app.py - Production Ready Slack Bot
import os
import re
import logging
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# DB Connection
from core.db_conn import get_conn, put_conn

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("slackbot")

# ENV Check
REQUIRED_VARS = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "DATABASE_URL"]
missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
if missing:
    raise RuntimeError(f"❌ Missing ENV vars: {', '.join(missing)}")

logger.info("✓ All ENV vars present")

# ═══════════════════════════════════════════════════════════════════════
# Slack Bolt App
# ═══════════════════════════════════════════════════════════════════════
bolt_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    process_before_response=True  # Important for Render timeout
)

# ═══════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════

def parse_search(text: str) -> dict:
    """
    Parse /jobs command text:
      /jobs python
      /jobs berlin python
      /jobs "data analyst" remote
    """
    text = (text or "").strip().lower()
    result = {"q": None, "loc": None, "remote": False}
    
    if not text:
        return result
    
    # Check for "remote" keyword
    if "remote" in text:
        result["remote"] = True
        text = text.replace("remote", "").strip()
    
    # Handle quoted strings
    quoted = re.findall(r'"([^"]+)"', text)
    rest = re.sub(r'"[^"]+"', "", text).split()
    tokens = [*quoted, *rest]
    tokens = [t.strip() for t in tokens if t.strip()]
    
    # First token = search query, second = location
    if tokens:
        result["q"] = tokens[0]
    if len(tokens) > 1:
        result["loc"] = tokens[1]
    
    logger.info(f"Parsed search: {result}")
    return result


def fetch_jobs(q=None, loc=None, remote=False, limit=10):
    """Query jobs from database with filters."""
    clauses = []
    params = []
    
    if q:
        like = f"%{q}%"
        clauses.append("(LOWER(title) LIKE %s OR LOWER(company) LIKE %s)")
        params.extend([like, like])
    
    if loc:
        clauses.append("LOWER(COALESCE(location, '')) LIKE %s")
        params.append(f"%{loc}%")
    
    if remote:
        clauses.append("LOWER(COALESCE(remote, '')) = 'remote'")
    
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    
    sql = f"""
        SELECT 
            title,
            company,
            location,
            url,
            posted_at::text
        FROM jobs
        {where}
        ORDER BY posted_at DESC NULLS LAST
        LIMIT %s
    """
    params.append(limit)
    
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        logger.info(f"DB query returned {len(rows)} jobs")
        return rows
    except Exception as e:
        logger.error(f"DB error: {e}", exc_info=True)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            put_conn(conn)


def make_blocks(rows):
    """Build Slack Block Kit from job rows."""
    if not rows:
        return [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "❌ Keine Jobs gefunden. Versuche:\n"
                        "• `/jobs python`\n"
                        "• `/jobs berlin remote`\n"
                        "• `/jobs \"data analyst\"`"
            }
        }]
    
    blocks = [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*{len(rows)} Jobs gefunden:*"
        }
    }]
    
    for title, company, location, url, posted_at in rows:
        title = title or "Ohne Titel"
        company = company or "Unbekannt"
        location = location or "Remote"
        posted_at = posted_at or ""
        
        text = f"*{title}*\n{company} · {location}"
        if posted_at:
            text += f" · {posted_at[:10]}"
        if url:
            text += f"\n<{url}|→ Zur Stelle>"
        
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        blocks.append({"type": "divider"})
    
    # Remove last divider
    if len(blocks) > 1:
        blocks.pop()
    
    return blocks


# ═══════════════════════════════════════════════════════════════════════
# Slash Command Handler
# ═══════════════════════════════════════════════════════════════════════

@bolt_app.command("/jobs")
def handle_jobs(ack, respond, command, logger):
    """
    Handle /jobs slash command.
    Must ack() within 3 seconds!
    """
    # CRITICAL: Acknowledge immediately
    ack()
    
    user = command.get("user_name", "unknown")
    text = command.get("text", "")
    logger.info(f"/jobs called by {user}: '{text}'")
    
    try:
        # Parse search
        params = parse_search(text)
        
        # Query database
        rows = fetch_jobs(
            q=params["q"],
            loc=params["loc"],
            remote=params["remote"],
            limit=10
        )
        
        # Build response
        blocks = make_blocks(rows)
        
        # Send response
        respond(blocks=blocks, response_type="ephemeral")
        logger.info(f"✓ Response sent to {user}")
        
    except Exception as e:
        logger.error(f"Command error: {e}", exc_info=True)
        respond(
            text="⚠️ Fehler beim Abrufen der Jobs. Bitte später versuchen.",
            response_type="ephemeral"
        )


# ═══════════════════════════════════════════════════════════════════════
# Flask App & Routes
# ═══════════════════════════════════════════════════════════════════════

flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Main Slack events endpoint."""
    logger.info(f"Received POST to /slack/events")
    return handler.handle(request)


@flask_app.route("/slack/commands", methods=["POST"])
def slack_commands():
    """Alternative endpoint for slash commands."""
    logger.info(f"Received POST to /slack/commands")
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
@flask_app.route("/healthz", methods=["GET"])
def health():
    """Health check with DB probe."""
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "db": str(e)}), 500
    finally:
        put_conn(conn)


@flask_app.route("/", methods=["GET"])
def root():
    """Root endpoint."""
    return "JobScout Slackbot ✓", 200


# ═══════════════════════════════════════════════════════════════════════
# ASGI Wrapper for Uvicorn
# ═══════════════════════════════════════════════════════════════════════

from asgiref.wsgi import WsgiToAsgi
asgi_app = WsgiToAsgi(flask_app)


# ═══════════════════════════════════════════════════════════════════════
# Main (for local testing)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starting Flask server on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=True)