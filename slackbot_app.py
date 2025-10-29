# slackbot_app.py
# Zweck: Stabiler Slack-"Leser" Service. Nutzt Neon über core/db_conn,
# antwortet sofort mit ack(), keine Producer-Logik, keine localhost-DB.

import os
import re
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# ── DB aus zentralem Modul holen ────────────────────────────────────────────
# Wichtig: core/db_conn.py muss DATABASE_URL aus Env lesen und sslmode=require setzen.
from core.db_conn import get_conn, put_conn

# ── Pflicht-Env-Variablen prüfen ────────────────────────────────────────────
for k in ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]:
    if not os.environ.get(k):
        raise RuntimeError(f"Missing env var: {k}")

# ── Slack Bolt App ──────────────────────────────────────────────────────────
bolt_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

# ── Mini-Parser für /jobs Suchtext ──────────────────────────────────────────
def _sanitize(s: str | None) -> str:
    return (s or "").strip()

def parse_search(text: str) -> dict:
    """
    Muster:
      /jobs
      /jobs python
      /jobs "data analyst" berlin remote
    Logik:
      erstes Keyword -> q
      zweites Keyword -> loc
      Wort 'remote' -> Remote-Filter
    """
    t = _sanitize(text)
    out = {"q": None, "loc": None, "want_remote": False}
    if not t:
        return out

    want_remote = "remote" in t.lower()
    # Zitate berücksichtigen
    quoted = re.findall(r'"([^"]+)"', t)
    noquotes = re.sub(r'"[^"]+"', "", t).split()
    tokens = [*quoted, *noquotes]
    tokens = [x for x in (x.strip() for x in tokens) if x and x.lower() != "remote"]

    if tokens:
        out["q"] = tokens[0]
    if len(tokens) > 1:
        out["loc"] = tokens[1]
    out["want_remote"] = want_remote
    return out

def make_blocks(rows: list[tuple]) -> list[dict]:
    """Erwartet (title, company, location, url, posted_at::text). Baut Block Kit."""
    blocks: list[dict] = []
    for title, company, location, url, posted_at in rows:
        title = _sanitize(title) or "Ohne Titel"
        company = _sanitize(company) or "Unbekannt"
        location = _sanitize(location) or "Remote/Unbekannt"
        url = _sanitize(url) or ""
        meta = f"{company} · {location}"
        if posted_at:
            meta += f" · {posted_at}"
        text = f"*{title}*\n{meta}"
        if url:
            text += f"\n<{url}|Stellenanzeige öffnen>"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        blocks.append({"type": "divider"})
    if blocks:
        blocks.pop()
    return blocks

# ── Slash Command /jobs ─────────────────────────────────────────────────────
@bolt_app.command("/jobs")
def handle_jobs(ack, respond, command):
    # Sofort bestätigen, damit Slack nicht nach 3s abbricht
    ack()

    params = parse_search(command.get("text") or "")
    clauses = []
    sql_params = []

    if params["q"]:
        like = f"%{params['q'].lower()}%"
        clauses.append("(LOWER(title) LIKE %s OR LOWER(company) LIKE %s)")
        sql_params.extend([like, like])

    if params["loc"]:
        clauses.append("LOWER(COALESCE(location,'')) LIKE %s")
        sql_params.append(f"%{params['loc'].lower()}%")

    if params["want_remote"]:
        clauses.append("LOWER(COALESCE(remote,'')) = 'remote'")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT
            title,
            company,
            location,
            url,
            to_char(posted_at, 'YYYY-MM-DD') AS posted_at
        FROM jobs
        {where_sql}
        ORDER BY posted_at DESC NULLS LAST
        LIMIT 10
    """

    conn = None
    try:
        conn = get_conn()
        with conn, conn.cursor() as cur:
            cur.execute(sql, tuple(sql_params))
            rows = cur.fetchall()
    finally:
        put_conn(conn)

    if not rows:
        respond("Aucune offre trouvée. Essaye `/jobs python`, `/jobs \"data analyst\" remote` ou `/jobs berlin`.")
        return

    respond(blocks=make_blocks(rows))

# ── Flask Adapter & Healthchecks ────────────────────────────────────────────
flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

@flask_app.post("/slack/events")
def slack_events():
    return handler.handle(request)

@flask_app.get("/healthz")
def healthz():
    # Schneller Endpunkt, plus Mini-DB-Probe
    conn = None
    try:
        conn = get_conn()
        with conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return "ok", 200
    except Exception as e:
        return f"db_error: {e}", 500
    finally:
        put_conn(conn)

@flask_app.get("/")
def root():
    return "jobscout-daily slackbot up", 200

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))
