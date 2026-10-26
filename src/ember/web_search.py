"""Parse explicit requests to search the web from Ember's conversation."""

from __future__ import annotations

from dataclasses import dataclass
import re


_SEARCH_PATTERN = re.compile(
    r"(?:ابحث(?:ي|وا|لي)?(?:\s+عن)?|دور(?:ي)?\s+على|search(?:\s+for)?|look\s+up)\s+(.+)$",
    re.IGNORECASE,
)
_HOST_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z]{2,})+)",
    re.IGNORECASE,
)
_OPEN_CHROME_PATTERN = re.compile(
    r"^\s*(?:(?:please|can you)\s+)?(?:open|launch|start)\s+"
    r"(?:(?:google)\s+)?chrome(?:\s+browser)?[.!?]*\s*$"
    r"|^\s*(?:ممكن\s+)?(?:افتح|شغل|شغّل)\s+"
    r"(?:(?:جوجل)\s+)?كروم[.!؟?]*\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class WebSearchRequest:
    query: str
    host: str = ""


def is_direct_chrome_open_request(message: str) -> bool:
    return _OPEN_CHROME_PATTERN.fullmatch(message) is not None


def parse_web_search_request(message: str) -> WebSearchRequest | None:
    match = _SEARCH_PATTERN.search(message)
    if match is None:
        return None
    query = match.group(1).strip().rstrip(".!؟?,،")
    if not query or query.casefold() in {"for", "عن", "على"}:
        return None
    host_match = _HOST_PATTERN.search(message)
    return WebSearchRequest(
        query=query,
        host=host_match.group(1).lower() if host_match is not None else "",
    )
