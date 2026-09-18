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

## Landing Page

Mit den explizit erlaubten Quellen aus einer Konfiguration startet die lokale Webseite:

```sh
PYTHONPATH=src python -m person_scan.web example.config.json
```

Danach `http://127.0.0.1:8080` öffnen. Lokal wird der vollständige Scan der
konfigurierten Quellen verwendet. Auf GitHub Pages sucht die Oberfläche nur in
der öffentlichen Wikimedia/Wikipedia-Suche und markiert Ergebnisse zur
manuellen Prüfung; sie erstellt keine privaten Personendossiers.

## GitHub Pages

Der Workflow in `.github/workflows/pages.yml` veröffentlicht den Inhalt von
`web/` automatisch bei jedem Push auf `main`. GitHub Pages führt den Python-
Scanner nicht aus; online zeigt die Seite deshalb die ausdrücklich in
`web/sources.json` konfigurierten Quellen zur manuellen Prüfung. Für echte
Scans muss der lokale Python-Server oder ein separat betriebener Backend-
Dienst verwendet werden.
