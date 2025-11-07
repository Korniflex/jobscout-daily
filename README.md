# 🚀 JobScout Daily - README für Data Analysts

## 📋 Was macht dieses Projekt?

**JobScout Daily** ist ein automatisiertes System, das täglich Jobangebote von verschiedenen Jobportalen sammelt, in einer Datenbank speichert und über einen Slackbot bereitstellt.

### Workflow im Überblick:
```
APIs (Remotive, Arbeitnow, Jobicy)
    ↓
Python sammelt Jobs (main.py)
    ↓
Normalisierung & Deduplizierung
    ↓
PostgreSQL Datenbank (Neon)
    ↓
Slackbot zeigt Jobs an
```

---

## 🏗️ Projektstruktur

```
JobScout/
├── adapters/              # API-Verbindungen
│   ├── API_remotive.py    # Remotive API
│   ├── API_arbeitnow.py   # Arbeitnow API
│   ├── API_jobicy.py      # Jobicy API
│   └── __init__.py
│
├── core/                  # Kern-Logik
│   ├── orchestrator.py    # Koordiniert alle API-Aufrufe
│   ├── normalizer.py      # Vereinheitlicht Daten
│   ├── schema.py          # Datenmodelle (Job, CommonQuery)
│   └── db_conn.py         # Datenbankverbindung
│
├── main.py            # ⭐ Hauptskript für täglichen Import
├── slackbot_app.py        # Slack-Integration
├── requirements_render.txt # Python-Abhängigkeiten
└── .github/workflows/     # Automatisierung
    └── daily_ingest.yaml  # Läuft täglich um 06:00 UTC
```

---

## 🔧 Wie funktioniert der Code?

### 1️⃣ **API-Adapter** (`adapters/`)

Jede Datei holt Jobs von einer spezifischen API:

```python
# Beispiel: API_remotive.py

def fetch_remotive(params: dict) -> list[dict]:
    """Holt Jobs von Remotive API"""
    r = requests.get(remotive_url, params=params)
    return r.json().get("jobs", [])

def normalize_remotive(job: dict) -> Job:
    """Wandelt API-Response in einheitliches Format um"""
    return {
        "id": f"remotive:{job.get('id')}",
        "source": "remotive",
        "title": job.get("title"),
        "company": job.get("company_name"),
        # ... weitere Felder
    }
```

**Warum Normalisierung?**
- Remotive sagt `company_name`, Arbeitnow sagt `company` → wir brauchen **ein** einheitliches Feld
- Jede API hat andere Feldnamen → Normalisierung macht alles einheitlich

---

### 2️⃣ **Orchestrator** (`core/orchestrator.py`)

Koordiniert alle API-Aufrufe:

```python
def load_params(cq: CommonQuery) -> dict:
    """Ruft alle APIs parallel auf"""
    return {
        "remotive_raw": fetch_remotive(...),
        "arbeitnow_raw": fetch_arbeitnow(...),
        "jobicy_raw": fetch_jobicy(...),
    }
```

**Was passiert hier?**
1. Du gibst Suchkriterien ein (z.B. "IT", "Berlin")
2. Orchestrator ruft **alle APIs gleichzeitig** auf
3. Ergebnis: Ein Dictionary mit allen rohen Daten

---

### 3️⃣ **Schema** (`core/schema.py`)

Definiert die Datenstruktur mit Pydantic:

```python
class Job(BaseModel):
    source: str          # Pflichtfeld
    id: str              # Pflichtfeld
    title: Optional[str] = None  # Optional
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None  # "Vollzeit", "Teilzeit"
    remote: Optional[str] = None    # wird zu work_mode in DB
    url: Optional[AnyHttpUrl] = None
    posted_at: Optional[str] = None
```

**Vorteile von Pydantic:**
- ✅ Validiert Datentypen automatisch
- ✅ Verhindert Fehler durch fehlende Felder
- ✅ Selbstdokumentierend

---

### 4️⃣ **Hauptskript** (`main.py`)

Das Herzstück - läuft täglich automatisch:

```python
def main():
    # 1. Mit Datenbank verbinden
    conn = get_conn()
    
    # 2. Jobs von APIs holen
    common_params = CommonQuery(category="IT", limit=100)
    all_raws = load_params(common_params)
    
    # 3. Normalisieren
    all_normalized = normalize_jobs(all_raws)
    
    # 4. In Datenbank speichern
    rows_inserted = upsert_jobs(all_normalized, cur, conn)
    
    # 5. Job-Typen normalisieren (Englisch → Deutsch)
    normalize_job_types(cur, conn)
```

**Wichtige Funktion: `upsert_jobs()`**
```python
def upsert_jobs(jobs: list[Job], cursor, conn) -> int:
    for job in jobs:
        # Erstelle Hash zur Duplikat-Erkennung
        hash_value = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        
        # INSERT mit ON CONFLICT → Duplikate werden ignoriert
        cursor.execute("""
            INSERT INTO jobs (...)
            VALUES (...)
            ON CONFLICT (hash_value) DO NOTHING
        """)
```

**Was macht `ON CONFLICT DO NOTHING`?**
- Verhindert doppelte Einträge
- Wenn ein Job schon existiert (gleicher Hash) → überspringen
- Kein Fehler, einfach ignorieren

---

### 5️⃣ **Slackbot** (`slackbot_app.py`)

Stellt Jobs über Slack bereit:

```python
@bolt_app.command("/jobs")
def cmd_jobs(ack, respond, command):
    # Parse User-Eingabe: /jobs berlin analyst
    location, search, work_mode = _split_text(command.get("text"))
    
    # Suche in DB
    rows = fetch_jobs_from_db(search, location, work_mode)
    
    # Formatiere als Slack Blocks
    blocks = format_jobs_blocks(rows)
    respond(blocks=blocks)
```

**Unterstützte Befehle:**
- `/jobs analyst` → sucht nach "analyst"
- `/jobs berlin analyst` → in Berlin
- `/jobs "data analyst"` → exakte Phrase (mit Quotes)
- `/jobs berlin analyst mode:remote` → nur Remote-Jobs

---

## 🗄️ Datenbankstruktur

### Tabelle: `jobs`

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | SERIAL | Auto-Increment ID |
| `source` | TEXT | API-Quelle (remotive, arbeitnow...) |
| `title` | TEXT | Jobtitel |
| `company` | TEXT | Firmenname |
| `location` | TEXT | Standort |
| `job_type` | TEXT | "Vollzeit", "Teilzeit", "Praktikum"... |
| `work_mode` | TEXT | "remote", "hybrid", "onsite" |
| `posted_at` | TIMESTAMP | Veröffentlichungsdatum |
| `url` | TEXT | Link zur Stelle |
| `hash_value` | TEXT | Eindeutiger Hash (für Duplikat-Check) |
| `created_at` | TIMESTAMP | Wann in DB eingefügt |

**Wichtig:** `hash_value` ist der Unique Constraint → verhindert Duplikate!

---

## 🤖 Automatisierung (GitHub Actions)

### Datei: `.github/workflows/daily_ingest.yaml`

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # Täglich um 06:00 UTC
  workflow_dispatch:      # Manuell triggern über Actions Tab

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
      - name: Setup Python
      - name: Install deps
      - name: Run ingest
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python main.py
```

**Was passiert hier?**
1. GitHub startet jeden Tag um 6 Uhr morgens eine virtuelle Maschine
2. Installiert Python + Dependencies
3. Führt `main.py` aus
4. Speichert neue Jobs in Neon-Datenbank

---

## 🔑 Environment Variables

Diese müssen in GitHub Secrets und Render/Neon gesetzt sein:

```bash
# Datenbank (Neon)
DATABASE_URL=postgresql://user:pass@host/db

# Slack Bot
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# Optional
USE_RUN_TABLE=1  # Logging in ingestion_runs Tabelle
```

**Wie setze ich Secrets?**
1. GitHub: Repository → Settings → Secrets → Actions
2. Render: Dashboard → Environment Variables

---

## 📊 Datenfluss-Beispiel

```
User sucht: /jobs berlin data analyst mode:remote

    ↓

Slackbot parsed Input:
  location = "berlin"
  search = "data analyst"
  work_mode = "remote"

    ↓

SQL Query:
  SELECT * FROM jobs
  WHERE location ILIKE '%berlin%'
    AND (title ILIKE '%data analyst%' OR company ILIKE '%data analyst%')
    AND (job_type ILIKE '%remote%' OR title ILIKE '%remote%')
  ORDER BY id DESC
  LIMIT 10

    ↓

Slack zeigt 10 Ergebnisse + "Mehr anzeigen" Button
```

---

## 🚀 So startest du das Projekt lokal

### 1. Repository klonen
```bash
git clone <repo-url>
cd JobScout
```

### 2. Virtual Environment erstellen
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Dependencies installieren
```bash
pip install -r requirements_render.txt
```

### 4. `.env` Datei erstellen
```bash
DATABASE_URL=postgresql://...
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

### 5. Einmalig: Jobs importieren
```bash
python main.py
```

### 6. Slackbot starten
```bash
python slackbot_app.py
```

---

## 🐛 Häufige Probleme & Lösungen

### Problem: "No module named 'core'"
**Lösung:**
```bash
# Stelle sicher, dass du im Hauptverzeichnis bist
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Problem: "Connection refused" bei Datenbank
**Lösung:**
- Überprüfe `DATABASE_URL` in `.env`
- Teste Verbindung: `psql $DATABASE_URL`

### Problem: Slackbot antwortet nicht
**Lösung:**
1. Prüfe Slack App Konfiguration (Event Subscriptions)
2. Request URL muss öffentlich erreichbar sein (Render/ngrok)
3. Prüfe Logs: `heroku logs --tail` oder Render Dashboard

### Problem: Duplikate in der Datenbank
**Lösung:**
- Der Hash-Check sollte das verhindern
- Prüfe ob `hash_value` UNIQUE Constraint hat:
```sql
ALTER TABLE jobs ADD CONSTRAINT unique_hash UNIQUE (hash_value);
```

---

## 📈 Nächste Schritte / Erweiterungen

- [ ] Weitere APIs hinzufügen (LinkedIn, Indeed)
- [ ] Email-Alerts für neue Jobs
- [ ] Web-Dashboard (Flask/Streamlit)
- [ ] ML-basierte Job-Recommendations
- [ ] Salary-Parsing aus Beschreibungen

---

## 📚 Wichtige Konzepte für Anfänger

### 1. **API** (Application Programming Interface)
Eine Schnittstelle, über die Programme Daten austauschen. Wie ein Restaurant-Menü: Du bestellst (Request), die Küche liefert (Response).

### 2. **JSON** (JavaScript Object Notation)
```json
{
  "title": "Data Analyst",
  "company": "Google",
  "location": "Berlin"
}
```
Textformat für strukturierte Daten - wie Excel, aber für Maschinen.

### 3. **REST API**
Standard für Web-APIs. Du schickst HTTP-Anfragen (GET, POST, PUT, DELETE).

### 4. **Normalisierung**
Daten in ein einheitliches Format bringen:
```
API A: "company_name" → "company"
API B: "employer"     → "company"
API C: "organization" → "company"
```

### 5. **Hash**
Eindeutige "Fingerabdruck" für Daten. Gleiche Eingabe → gleicher Hash.
```python
hash("Google Data Analyst Berlin") → "a3f2..."
hash("Google Data Analyst Berlin") → "a3f2..."  # Immer gleich!
hash("Amazon Data Analyst Berlin") → "9d1e..."  # Unterschiedlich
```

### 6. **SQL Upsert**
"Update or Insert" - Update wenn existiert, Insert wenn neu:
```sql
INSERT INTO jobs (...) VALUES (...)
ON CONFLICT (hash_value) DO NOTHING
```

---

## 🆘 Hilfe & Support

- **Slack Channel:** #jobscout-support
- **GitHub Issues:** Für Bugs und Feature Requests
- **Code-Dokumentation:** Siehe Docstrings in den Funktionen

---

## 👥 Contributors

Erstellt von [Dein Team] - Data Analysts @ [Deine Firma]

**Happy Job Hunting! 🎯**


