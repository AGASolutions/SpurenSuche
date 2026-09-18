from __future__ import annotations

from http.client import HTTPConnection
from threading import Thread
from urllib.parse import urlencode
from unittest import TestCase
from unittest.mock import patch

from http.server import ThreadingHTTPServer

from person_scan.search import SearchResult
from person_scan.web import PersonScanHandler


class WebTests(TestCase):
    def test_scan_endpoint_returns_findings(self) -> None:
        result = SearchResult(
            source="Wikimedia / Wikipedia",
            url="https://de.wikipedia.org/wiki/Ada_Lovelace",
            title="Ada Lovelace",
            excerpt="Ada Lovelace",
            status="manual_review",
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), PersonScanHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch(
                "person_scan.web.search_public", return_value=[result]
            ) as mocked_search:
                connection = HTTPConnection("127.0.0.1", server.server_port)
                body = urlencode(
                    {
                        "name": "Ada Lovelace",
                        "birth_date": "1815-12-10",
                        "consent": "on",
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
            self.assertIn(
                "https://de.wikipedia.org/wiki/Ada_Lovelace", payload
            )
            mocked_search.assert_called_once()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    import unittest

    unittest.main()
