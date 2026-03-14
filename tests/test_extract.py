"""Tests for content URL extraction utilities."""

from openattribution.telemetry.extract import (
    extract_citation_urls,
    extract_indexed_citations,
    extract_result_urls,
)


# ---------------------------------------------------------------------------
# extract_citation_urls
# ---------------------------------------------------------------------------


class TestExtractCitationUrls:
    def test_extracts_markdown_links(self):
        text = "See [Wirecutter](https://example.com/review) for details"
        assert extract_citation_urls(text) == ["https://example.com/review"]

    def test_extracts_bare_urls(self):
        text = "Visit https://example.com today"
        assert extract_citation_urls(text) == ["https://example.com"]

    def test_strips_trailing_punctuation(self):
        text = "Visit https://example.com."
        assert extract_citation_urls(text) == ["https://example.com"]

    def test_deduplicates(self):
        text = "See [Example](https://example.com/review) and also https://example.com/review"
        result = extract_citation_urls(text)
        assert result == ["https://example.com/review"]
        assert len(result) == 1

    def test_empty_string(self):
        assert extract_citation_urls("") == []


# ---------------------------------------------------------------------------
# extract_result_urls
# ---------------------------------------------------------------------------


class TestExtractResultUrls:
    def test_extracts_url_property(self):
        results = [{"url": "https://a.com"}, {"url": "https://b.com"}]
        assert extract_result_urls(results) == ["https://a.com", "https://b.com"]

    def test_extracts_link_property(self):
        results = [{"link": "https://a.com"}]
        assert extract_result_urls(results) == ["https://a.com"]

    def test_skips_non_http(self):
        results = [{"url": "ftp://bad.com"}]
        assert extract_result_urls(results) == []

    def test_deduplicates(self):
        results = [{"url": "https://a.com"}, {"url": "https://a.com"}]
        result = extract_result_urls(results)
        assert result == ["https://a.com"]
        assert len(result) == 1


# ---------------------------------------------------------------------------
# extract_indexed_citations
# ---------------------------------------------------------------------------


class TestExtractIndexedCitations:
    def test_resolves_single_marker(self):
        sources = ["https://a.com", "https://b.com"]
        assert extract_indexed_citations("See [1] for details", sources) == [
            "https://a.com"
        ]

    def test_resolves_multiple_markers(self):
        sources = ["https://a.com", "https://b.com", "https://c.com"]
        text = "Policy announced [1] and expanded [3]."
        assert extract_indexed_citations(text, sources) == [
            "https://a.com",
            "https://c.com",
        ]

    def test_ignores_out_of_range(self):
        sources = ["https://a.com"]
        assert extract_indexed_citations("[0] and [2] and [1]", sources) == [
            "https://a.com"
        ]

    def test_deduplicates(self):
        sources = ["https://a.com", "https://b.com"]
        result = extract_indexed_citations("[1] then again [1]", sources)
        assert result == ["https://a.com"]
        assert len(result) == 1

    def test_accepts_dict_sources(self):
        sources: list[str | dict[str, object]] = [
            {"url": "https://a.com"},
            {"url": "https://b.com"},
        ]
        assert extract_indexed_citations("See [2]", sources) == ["https://b.com"]

    def test_skips_null_url(self):
        sources: list[str | dict[str, object]] = [
            {"url": None},
            {"url": "https://b.com"},
        ]
        assert extract_indexed_citations("[1] [2]", sources) == ["https://b.com"]

    def test_no_markers(self):
        assert extract_indexed_citations("No citations here", ["https://a.com"]) == []

    def test_empty_text(self):
        assert extract_indexed_citations("", ["https://a.com"]) == []

    def test_mixed_string_and_dict_sources(self):
        sources: list[str | dict[str, object]] = [
            "https://a.com",
            {"url": "https://b.com"},
        ]
        assert extract_indexed_citations("[1] [2]", sources) == [
            "https://a.com",
            "https://b.com",
        ]
