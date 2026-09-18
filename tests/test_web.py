from __future__ import annotations

from datetime import date
from http.client import HTTPConnection
from threading import Thread
from urllib.parse import urlencode
from unittest import TestCase
from unittest.mock import patch

from http.server import ThreadingHTTPServer

from person_scan.core import Finding, Source
from person_scan.web import PersonScanHandler


class WebTests(TestCase):
    def test_scan_endpoint_returns_findings(self) -> None:
        finding = Finding(
            source="Profil",
            url="https://example.org/profile",
            retrieved_at="2026-09-18T00:00:00+00:00",
            status="match",
            score=1.0,
            matched_fields=("name", "birth_date"),
            title="Öffentliches Profil",
            excerpt="Ada Lovelace",
        )
        PersonScanHandler.sources = [
            Source("Profil", "https://example.org/profile")
        ]
        server = ThreadingHTTPServer(("127.0.0.1", 0), PersonScanHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch(
                "person_scan.web.scan", return_value=[finding]
            ) as mocked_scan:
                connection = HTTPConnection("127.0.0.1", server.server_port)
                body = urlencode(
                    {
                        "name": "Ada Lovelace",
                        "birth_date": date(1815, 12, 10).isoformat(),
                    }
                )
                connection.request(
                    "POST",
                    "/scan",
                    body,
                    {"Content-Type": "application/x-www-form-urlencoded"},
                )
                response = connection.getresponse()
                payload = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("https://example.org/profile", payload)
            mocked_scan.assert_called_once()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    import unittest

    unittest.main()
