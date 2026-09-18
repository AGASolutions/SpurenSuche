from __future__ import annotations

from dataclasses import dataclass
from urllib import robotparser
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from .core import Source

USER_AGENT = "public-person-scan/0.1 (+configured-public-sources)"
MAX_BYTES = 2_000_000


@dataclass(frozen=True)
class FetchResult:
    html: str | None
    error: str | None = None


def fetch_source(source: Source, timeout: float = 10.0) -> FetchResult:
    parsed = urlparse(source.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return FetchResult(None, "Ungültige HTTP(S)-URL")

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    robots = robotparser.RobotFileParser(robots_url)
    try:
        robots.read()
    except OSError as error:
        return FetchResult(None, f"robots.txt nicht erreichbar: {error}")
    if not robots.can_fetch(USER_AGENT, source.url):
        return FetchResult(None, "Abruf durch robots.txt nicht erlaubt")

    request = Request(
        source.url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                return FetchResult(
                    None, f"Nicht unterstützter Inhaltstyp: {content_type}"
                )
            body = response.read(MAX_BYTES + 1)
    except OSError as error:
        return FetchResult(None, str(error))

    if len(body) > MAX_BYTES:
        return FetchResult(None, f"Antwort größer als {MAX_BYTES} Bytes")
    charset = response.headers.get_content_charset() or "utf-8"
    return FetchResult(body.decode(charset, errors="replace"))
