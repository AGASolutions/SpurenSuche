from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import re
from typing import Iterable


@dataclass(frozen=True)
class Subject:
    name: str
    birth_date: date


@dataclass(frozen=True)
class Source:
    name: str
    url: str


@dataclass(frozen=True)
class Finding:
    source: str
    url: str
    retrieved_at: str
    status: str
    score: float
    matched_fields: tuple[str, ...]
    title: str = ""
    excerpt: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self) | {"matched_fields": list(self.matched_fields)}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._ignored_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript", "template"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        ignored_tags = {"script", "style", "noscript", "template"}
        if tag in ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
        self.text_parts.append(cleaned)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts)

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def extract_page(html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.title, parser.text


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _date_patterns(subject: Subject) -> tuple[str, ...]:
    iso = subject.birth_date.isoformat()
    european = subject.birth_date.strftime("%d.%m.%Y")
    slash = subject.birth_date.strftime("%d/%m/%Y")
    return iso, european, slash


def assess_finding(
    subject: Subject,
    source: Source,
    title: str,
    text: str,
    retrieved_at: str | None = None,
) -> Finding:
    normalized_text = _normalized(text)
    normalized_name = _normalized(subject.name)
    matched: list[str] = []
    score = 0.0

    if normalized_name and normalized_name in normalized_text:
        matched.append("name")
        score += 0.6

    if any(
        _normalized(pattern) in normalized_text
        for pattern in _date_patterns(subject)
    ):
        matched.append("birth_date")
        score += 0.4
    elif str(subject.birth_date.year) in normalized_text and "name" in matched:
        matched.append("birth_year")
        score += 0.2

    if {"name", "birth_date"}.issubset(matched):
        status = "match"
    elif "name" in matched:
        status = "manual_review"
    else:
        status = "no_match"

    excerpt = _excerpt(text, subject.name)
    return Finding(
        source=source.name,
        url=source.url,
        retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat(),
        status=status,
        score=min(score, 1.0),
        matched_fields=tuple(matched),
        title=title,
        excerpt=excerpt,
    )


def _excerpt(text: str, needle: str, radius: int = 180) -> str:
    position = _normalized(text).find(_normalized(needle))
    if position < 0:
        return ""
    start = max(0, position - radius)
    end = min(len(text), position + len(needle) + radius)
    excerpt = " ".join(text[start:end].split())
    prefix = "..." if start else ""
    suffix = "..." if end < len(text) else ""
    return prefix + excerpt + suffix


def validate_sources(sources: Iterable[Source]) -> None:
    for source in sources:
        if not source.name.strip():
            raise ValueError("Jede Quelle braucht einen Namen.")
        if not re.match(r"^https?://", source.url, re.IGNORECASE):
            raise ValueError(f"Nur HTTP(S)-Quellen sind erlaubt: {source.url}")
