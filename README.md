<div style="background:#0b3d91;color:#fff;padding:12px;border-radius:6px;">
🚀 <strong>JobScout Daily</strong>
</div>

```bash
JobScout Daily sammelt täglich Jobs von verschiedenen Jobportalen.
│
├─ Jobangebote
│  ├─ für eine gewisse Anzahl an konkreten Jobtiteln die jeweils ersten X Treffer
│  ├─ Strukturierte Daten sind hier die Suchkriterien der verschiedenen Jobportale, die als gemeinsame, einheitliche Parameter festgelegt wurden, sowie die Ergebnisse der Suche.
│  └─ Die Normalisierung sorgt dafür, das die Jobangebote aus allen APIs zusammengefügt werden können.
│
├─ Datenbank
│  ├─ speichert die Inhalte der Jobangebote in einer Datenbank
│  ├─ Die Datenbank enthält die strukturierten und normalisierten Daten, aktualisiert sich selbst, erkennt und entfernt Duplikate.
│  └─ stellt die Jobangebote über einen Slackbot bereit
│
├─ Slackbot
│  └─ Der Slackbot greift auf die Datenbank zu, und zeigt die Ergebnisse an.
│
├─ Nutzer
│  └─ können in Slack nach Stadt, Jobtitel und Arbeitsmodus (remote/vor Ort) filtern.
│
└─ Anforderungen
   ├─ Python
   ├─ Pandas
   └─ PostgreSQL
```
