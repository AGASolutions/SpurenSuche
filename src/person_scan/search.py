from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .core import Source, Subject, assess_finding


@dataclass(frozen=True)
class SearchRequest:
    subject: Subject
    email: str | None


@dataclass(frozen=True)
class SearchResult:
    source: str
    url: str
    title: str
    excerpt: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "excerpt": self.excerpt,
            "status": self.status,
        }


def validate_request(
    name: str, birth_date: str, email: str | None
) -> SearchRequest:
    cleaned_name = " ".join(name.split())
    if not cleaned_name or len(cleaned_name) > 160:
        raise ValueError("Bitte einen gültigen Namen eingeben.")
    try:
        from datetime import date

        parsed_date = date.fromisoformat(birth_date)
    except ValueError as error:
        raise ValueError("Das Geburtsdatum muss gültig sein.") from error
    cleaned_email = (email or "").strip().lower() or None
    if cleaned_email and (
        len(cleaned_email) > 254
        or "@" not in cleaned_email
        or " " in cleaned_email
    ):
        raise ValueError("Bitte eine gültige E-Mail-Adresse eingeben.")
    return SearchRequest(Subject(cleaned_name, parsed_date), cleaned_email)


def _request_json(
    url: str,
    params: dict[str, str],
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    query = urlencode(params)
    request = Request(
        f"{url}?{query}",
        headers={"User-Agent": "trace-public-search/0.2", **(headers or {})},
    )
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def _wikipedia_results(request: SearchRequest) -> list[SearchResult]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f'"{request.subject.name}"',
        "srnamespace": "0",
        "srlimit": "10",
        "srprop": "snippet",
        "format": "json",
        "origin": "*",
    }
    data = _request_json("https://de.wikipedia.org/w/api.php", params)
    query = data.get("query", {})
    items = query.get("search", []) if isinstance(query, dict) else []
    results: list[SearchResult] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", ""))
        snippet = str(item.get("snippet", ""))
        text = snippet.replace(
            "<span class=\"searchmatch\">", ""
        ).replace("</span>", "")
        source = Source("Wikimedia / Wikipedia", "https://de.wikipedia.org")
        finding = assess_finding(request.subject, source, title, text)
        results.append(
            SearchResult(
                source=finding.source,
                url=f"https://de.wikipedia.org/wiki/{title.replace(' ', '_')}",
                title=title,
                excerpt=text,
                status=finding.status,
            )
        )
    return results


def _brave_results(request: SearchRequest) -> list[SearchResult]:
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return []
    query = (
        f'"{request.subject.name}" '
        f'"{request.subject.birth_date.isoformat()}"'
    )
    data = _request_json(
        "https://api.search.brave.com/res/v1/web/search",
        {"q": query, "count": "10", "safesearch": "moderate"},
        {"Accept": "application/json", "X-Subscription-Token": api_key},
    )
    web = data.get("web", {})
    items = web.get("results", []) if isinstance(web, dict) else []
    return [
        SearchResult(
            source="Brave Search",
            url=str(item.get("url", "")),
            title=str(item.get("title", "")),
            excerpt=str(item.get("description", "")),
            status="manual_review",
        )
        for item in items
        if isinstance(item, dict) and item.get("url")
    ]


def search_public(request: SearchRequest) -> list[SearchResult]:
    results: list[SearchResult] = []
    providers = (_wikipedia_results, _brave_results)
    for provider in providers:
        try:
            results.extend(provider(request))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    unique: dict[str, SearchResult] = {}
    for result in results:
        unique.setdefault(result.url, result)
    return list(unique.values())
