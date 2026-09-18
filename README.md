# Public Person Scan

Kleines, datensparsames MVP zur Prüfung der eigenen öffentlichen Profile in ausdrücklich konfigurierten Quellen.

## Grenzen

- Es werden nur die in der Konfiguration genannten HTTP(S)-URLs abgerufen.
- `robots.txt`, ein User-Agent und ein Antwortlimit werden berücksichtigt.
- Es gibt keine Suchmaschinenabfrage, keinen Login, keine Paywall- oder Captcha-Umgehung.
- Ein Name ohne exaktes Geburtsdatum ergibt nur `manual_review`, niemals automatisch `match`.
- Der Bericht ist eine Quellenliste und kein Vollständigkeitsnachweis.

## Start

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
person-scan example.config.json -o report.json
```

Die Datei `example.config.json` muss vor dem Abruf durch eigene Daten und ausdrücklich erlaubte öffentliche Quellen ersetzt werden. Keine fremden oder sensiblen Personendaten eintragen.

## Tests

```sh
PYTHONPATH=src python -m unittest discover -s tests -q
```

## Landing Page und Backend

Mit den explizit erlaubten Quellen aus einer Konfiguration startet die lokale Webseite:

```sh
PYTHONPATH=src python -m person_scan.web example.config.json
```

Danach `http://127.0.0.1:8080` öffnen. Der Server-Endpunkt `POST /scan`
validiert Name, Geburtsdatum, optionale E-Mail und die Eigennutzungs-
bestätigung. Er fragt öffentliche Provider ab und speichert weder Anfragen
noch Ergebnisse.

Für die Online-Version muss der Python-Service separat gehostet werden, da
GitHub Pages kein Backend ausführt. Eine Render-Konfiguration liegt in
`render.yaml`. Nach dem Deployment die öffentliche Backend-URL in
`web/config.js` als `window.TRACE_API_URL` eintragen und nach `main` pushen.

## GitHub Pages

Der Workflow in `.github/workflows/pages.yml` veröffentlicht den Inhalt von
`web/` automatisch bei jedem Push auf `main`. GitHub Pages hostet nur das
Frontend; die serverseitige Suche läuft über `TRACE_API_URL`. Ohne gesetzte
Backend-URL verwendet die Seite weiterhin den öffentlichen Wikimedia-
Fallback und markiert Treffer zur manuellen Prüfung.

Optional kann mit `BRAVE_SEARCH_API_KEY` ein zusätzlicher Brave-Provider im
Backend aktiviert werden. Der Schlüssel gehört ausschließlich in die
Umgebungsvariablen des Backend-Hosters, niemals in `web/config.js`.
