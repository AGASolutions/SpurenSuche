from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .cli import _load_config, scan
from .core import Subject

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"


class PersonScanHandler(BaseHTTPRequestHandler):
    sources = []

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            body = (WEB_DIR / "index.html").read_bytes()
            self._send(200, "text/html; charset=utf-8", body)
            return
        if self.path == "/static/styles.css":
            body = (WEB_DIR / "styles.css").read_bytes()
            self._send(200, "text/css; charset=utf-8", body)
            return
        if self.path == "/static/app.js":
            body = (WEB_DIR / "app.js").read_bytes()
            self._send(200, "text/javascript; charset=utf-8", body)
            return
        if self.path == "/sources.json":
            body = (WEB_DIR / "sources.json").read_bytes()
            self._send(200, "application/json; charset=utf-8", body)
            return
        self._send(404, "text/plain; charset=utf-8", b"Not found")

    def do_POST(self) -> None:
        if self.path != "/scan":
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        fields = parse_qs(self.rfile.read(length).decode("utf-8"))
        name = fields.get("name", [""])[0].strip()
        birth_date = fields.get("birth_date", [""])[0].strip()
        if not name or not birth_date:
            self._json(
                400, {"error": "Name und Geburtsdatum sind erforderlich."}
            )
            return
        try:
            subject = Subject(
                name=name, birth_date=date.fromisoformat(birth_date)
            )
        except ValueError:
            self._json(400, {"error": "Das Geburtsdatum muss gültig sein."})
            return

        findings = [
            finding.to_dict() for finding in scan(subject, self.sources)
        ]
        self._json(
            200,
            {
                "subject": {"name": subject.name},
                "scope": "Konfigurierte öffentliche Quellen",
                "findings": findings,
            },
        )

    def _json(self, status: int, data: dict[str, object]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", body)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(
    config_path: Path, host: str = "127.0.0.1", port: int = 8080
) -> None:
    _, sources = _load_config(config_path)
    PersonScanHandler.sources = sources
    server = ThreadingHTTPServer((host, port), PersonScanHandler)
    print(f"Person Scan läuft auf http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Startet die Public-Person-Scan-Webseite."
    )
    parser.add_argument(
        "config", type=Path, help="JSON-Datei mit erlaubten Quellen"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    serve(args.config, args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
