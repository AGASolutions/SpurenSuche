from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path

from .core import (
    Finding,
    Source,
    Subject,
    assess_finding,
    extract_page,
    validate_sources,
)
from .fetch import fetch_source


def _load_config(path: Path) -> tuple[Subject, list[Source]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    subject = Subject(
        name=data["subject"]["name"],
        birth_date=date.fromisoformat(data["subject"]["birth_date"]),
    )
    sources = [
        Source(name=item["name"], url=item["url"])
        for item in data["sources"]
    ]
    validate_sources(sources)
    return subject, sources


def scan(subject: Subject, sources: list[Source]) -> list[Finding]:
    findings: list[Finding] = []
    for source in sources:
        fetched = fetch_source(source)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        if fetched.html is None:
            findings.append(
                Finding(
                    source.name,
                    source.url,
                    retrieved_at,
                    "unavailable",
                    0.0,
                    (),
                    excerpt=fetched.error or "",
                )
            )
            continue
        title, text = extract_page(fetched.html)
        findings.append(
            assess_finding(subject, source, title, text, retrieved_at)
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prüft konfigurierte öffentliche Quellen auf eigene Profile."
        )
    )
    parser.add_argument(
        "config",
        type=Path,
        help="JSON-Datei mit subject und expliziten sources",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Ziel für den JSON-Bericht; Standard: stdout",
    )
    args = parser.parse_args()

    subject, sources = _load_config(args.config)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject": {
            "name": subject.name,
            "birth_date": subject.birth_date.isoformat(),
        },
        "scope": "Nur konfigurierte, öffentlich zugängliche HTTP(S)-Quellen",
        "findings": [finding.to_dict() for finding in scan(subject, sources)],
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
