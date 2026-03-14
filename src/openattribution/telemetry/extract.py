"""
OpenAttribution Telemetry - content URL extraction utilities.

Helpers for extracting content URLs from AI-generated text, so they
can be recorded as telemetry events without manual instrumentation.
"""

from __future__ import annotations

import re

# Matches [text](url) - standard Markdown links.
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")

# Matches bare URLs starting with http/https.
_BARE_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")

# Matches [n] citation markers (1-indexed).
_INDEXED_CITATION_RE = re.compile(r"\[(\d+)\]")

# Trailing punctuation that commonly attaches to bare URLs.
_TRAILING_PUNCT_RE = re.compile(r"[.,;:!?]+$")


def extract_citation_urls(text: str) -> list[str]:
    """Extract all HTTP/HTTPS URLs from Markdown-formatted text.

    Finds URLs in two forms:

    - Markdown links: ``[anchor text](https://...)``
    - Bare URLs: ``https://...``

    Results are deduplicated. Useful for extracting citation URLs from
    AI model responses that include web search results.

    Example::

        >>> extract_citation_urls("See [Wirecutter](https://example.com/review)")
        ['https://example.com/review']
    """
    urls: dict[str, None] = {}  # ordered set

    for match in _MARKDOWN_LINK_RE.finditer(text):
        url = _clean_url(match.group(2))
        urls[url] = None

    for match in _BARE_URL_RE.finditer(text):
        url = _clean_url(match.group(0))
        urls[url] = None

    return list(urls)


def extract_result_urls(
    results: list[dict[str, object]],
) -> list[str]:
    """Extract URLs from a list of search result objects.

    Accepts any dict with a ``url`` or ``link`` string value - works with
    most search API responses.

    Example::

        >>> extract_result_urls([{"url": "https://a.com"}, {"url": "https://b.com"}])
        ['https://a.com', 'https://b.com']
    """
    urls: dict[str, None] = {}
    for r in results:
        url = r.get("url") or r.get("link")
        if isinstance(url, str) and url.startswith("http"):
            urls[url] = None
    return list(urls)


def extract_indexed_citations(
    text: str,
    sources: list[str | dict[str, object]],
) -> list[str]:
    """Resolve ``[n]`` citation markers to URLs using a numbered source list.

    Many RAG systems (Perplexity, ChatGPT with search, custom agents) cite
    sources with ``[1]``, ``[2]``, etc. that map to a list of retrieved
    articles. This function parses those markers and resolves them to URLs.

    Sources can be plain URL strings or dicts with a ``url`` key, covering
    both simple lists and richer result objects.

    Markers are 1-indexed (as is convention in AI responses). Out-of-range
    indices are silently ignored. Results are deduplicated.

    Example::

        >>> sources = ["https://a.com", "https://b.com", "https://c.com"]
        >>> extract_indexed_citations("Announced [1] and expanded [3].", sources)
        ['https://a.com', 'https://c.com']
    """
    urls: dict[str, None] = {}

    for match in _INDEXED_CITATION_RE.finditer(text):
        idx = int(match.group(1)) - 1  # [1]-indexed -> 0-indexed
        if idx < 0 or idx >= len(sources):
            continue

        source = sources[idx]
        if isinstance(source, str):
            url: str | None = source
        else:
            val = source.get("url")
            url = val if isinstance(val, str) else None

        if url is not None:
            urls[url] = None

    return list(urls)


def _clean_url(url: str) -> str:
    """Remove trailing punctuation that commonly attaches to bare URLs."""
    return _TRAILING_PUNCT_RE.sub("", url)
