"""Fetch and extract SEO signals from a target website (no manual keywords required)."""

from __future__ import annotations

import json
import re
from collections import Counter
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx

_FETCH_TIMEOUT = 15.0
_MAX_HTML_BYTES = 512_000
_MAX_TEXT_CHARS = 12_000
_USER_AGENT = (
    "Mozilla/5.0 (compatible; AgentNexus-SEO/1.0; +https://agentnexus.mrgeo888.workers.dev)"
)

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are", "was", "have",
    "has", "had", "not", "but", "all", "can", "will", "our", "their", "they", "them", "been",
    "being", "were", "what", "when", "where", "which", "while", "who", "whom", "whose", "why",
    "how", "into", "about", "after", "before", "between", "through", "during", "each", "more",
    "most", "other", "some", "such", "only", "own", "same", "than", "too", "very", "just", "also",
    "now", "new", "get", "may", "use", "using", "used", "www", "com", "http", "https", "home",
    "page", "click", "here", "read", "learn", "contact", "welcome", "site", "website",
}

_META_RE = re.compile(
    r'<meta\s+(?:[^>]*?\s)?(?:name|property)=["\']([^"\']+)["\']\s+'
    r'(?:[^>]*?\s)?content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)
_META_CONTENT_FIRST_RE = re.compile(
    r'<meta\s+(?:[^>]*?\s)?content=["\']([^"\']*)["\']\s+'
    r'(?:[^>]*?\s)?(?:name|property)=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_H_RE = re.compile(r"<h([1-3])[^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
_LINK_RE = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"\s+")

_CSS_JUNK = {
    "ast", "builder", "template", "container", "sidebar", "entry", "content", "margin",
    "padding", "font", "size", "width", "max", "min", "flex", "grid", "display", "block",
    "inline", "color", "background", "border", "radius", "hover", "active", "focus",
    "input", "type", "text", "field", "form", "button", "widget", "elementor", "woocommerce",
    "wp", "class", "style", "media", "query", "screen", "mobile", "tablet", "desktop",
    "separate", "wrap", "column", "row", "align", "justify", "center", "left", "right",
}


def _strip_tags(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _html_to_content_text(html: str) -> str:
    """Visible content only — drop script/style blocks that pollute keyword extraction."""
    cleaned = _SCRIPT_STYLE_RE.sub(" ", html)
    return _strip_tags(cleaned)


def _parse_meta_tags(html: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for pattern in (_META_RE, _META_CONTENT_FIRST_RE):
        for match in pattern.finditer(html):
            if pattern is _META_RE:
                name, content = match.group(1).lower(), match.group(2)
            else:
                content, name = match.group(1), match.group(2).lower()
            if name and content and name not in meta:
                meta[name] = unescape(content).strip()
    return meta


def _extract_headings(html: str) -> list[dict[str, str]]:
    headings: list[dict[str, str]] = []
    for match in _H_RE.finditer(html):
        level = match.group(1)
        text = _strip_tags(match.group(2))
        if text and len(text) < 200:
            headings.append({"level": f"h{level}", "text": text})
        if len(headings) >= 20:
            break
    return headings


def _extract_internal_links(html: str, base_url: str) -> list[str]:
    host = urlparse(base_url).netloc.lower()
    paths: list[str] = []
    seen: set[str] = set()
    for match in _LINK_RE.finditer(html):
        href = match.group(1).strip()
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc.lower() != host:
            continue
        path = parsed.path or "/"
        if path not in seen:
            seen.add(path)
            paths.append(path)
        if len(paths) >= 30:
            break
    return paths


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z\u0E00-\u0E7F]{3,}", text.lower())


def _is_junk_token(token: str) -> bool:
    return token in _STOPWORDS or token in _CSS_JUNK or token.isdigit() or len(token) < 3


def _extract_keywords_from_sources(
    *,
    title: str,
    meta_description: str,
    headings: list[dict[str, str]],
    body_text: str,
    limit: int = 15,
) -> list[dict[str, str | int]]:
    weighted_parts: list[tuple[str, float]] = [
        (title, 5.0),
        (meta_description, 4.0),
    ]
    for h in headings:
        weighted_parts.append((h["text"], 3.0 if h["level"] == "h1" else 2.5))
    weighted_parts.append((body_text[:4000], 1.0))

    unigrams: Counter[str] = Counter()
    bigrams: Counter[str] = Counter()

    for text, weight in weighted_parts:
        if not text:
            continue
        tokens = [t for t in _tokenize(text) if not _is_junk_token(t)]
        for token in tokens:
            unigrams[token] += int(weight)
        for i in range(len(tokens) - 1):
            a, b = tokens[i], tokens[i + 1]
            if not _is_junk_token(a) and not _is_junk_token(b):
                bigrams[f"{a} {b}"] += int(weight)

    scored: list[tuple[float, str, int, str]] = []
    for word, score in unigrams.most_common(50):
        if score < 2:
            continue
        scored.append((score * 1.0, word, score, "unigram"))
    for phrase, score in bigrams.most_common(30):
        if score < 3:
            continue
        if any(part in _CSS_JUNK for part in phrase.split()):
            continue
        scored.append((score * 2.0, phrase, score, "bigram"))

    scored.sort(reverse=True)
    results: list[dict[str, str | int]] = []
    seen: set[str] = set()
    for _, term, count, kind in scored:
        if term in seen:
            continue
        seen.add(term)
        results.append({"term": term, "count": count, "type": kind})
        if len(results) >= limit:
            break
    return results


def _infer_intent(keywords: list[dict[str, str | int]], headings: list[dict[str, str]]) -> str:
    commercial = {"pricing", "price", "buy", "shop", "order", "quote", "service", "services"}
    local = {"near", "location", "locations", "city", "branch"}
    terms = {str(k["term"]).lower() for k in keywords}
    heading_text = " ".join(h["text"].lower() for h in headings)
    if terms & commercial or any(w in heading_text for w in commercial):
        return "commercial / transactional"
    if terms & local:
        return "local / geo-targeted"
    if any(w in heading_text for w in ("blog", "guide", "how", "what", "tips")):
        return "informational"
    return "mixed / branded"


async def _fetch_html(url: str) -> tuple[str | None, str | None, int | None]:
    try:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        ) as client:
            response = await client.get(url)
            status = response.status_code
            if status >= 400:
                return None, f"HTTP {status}", status
            content_type = (response.headers.get("content-type") or "").lower()
            if "html" not in content_type and "text/" not in content_type:
                return None, f"Non-HTML content-type: {content_type}", status
            raw = response.content[:_MAX_HTML_BYTES]
            html = raw.decode(response.encoding or "utf-8", errors="replace")
            return html, None, status
    except Exception as exc:
        return None, str(exc), None


async def _web_context(query: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None

    abstract = payload.get("AbstractText") or ""
    related = [
        item.get("Text", "")
        for item in payload.get("RelatedTopics", [])
        if isinstance(item, dict) and item.get("Text")
    ][:5]
    if not abstract and not related:
        return None
    parts = [f"Query: {query}"]
    if abstract:
        parts.append(f"Summary: {abstract}")
    if related:
        parts.append("Related: " + " | ".join(related))
    return "\n".join(parts)


async def gather_site_intelligence(url: str, *, lang: str = "en") -> dict:
    """Crawl target homepage and extract keywords, on-page signals, and web context."""
    html, fetch_error, status = await _fetch_html(url)
    result: dict = {
        "url": url,
        "final_url": url,
        "http_status": status,
        "fetch_error": fetch_error,
        "lang_hint": lang,
    }

    if not html:
        result["keywords"] = []
        result["warning"] = fetch_error or "Could not fetch homepage"
        return result

    meta = _parse_meta_tags(html)
    title_match = _TITLE_RE.search(html)
    title = _strip_tags(title_match.group(1)) if title_match else ""
    headings = _extract_headings(html)
    body_text = _html_to_content_text(html)[:_MAX_TEXT_CHARS]
    keywords = _extract_keywords_from_sources(
        title=title,
        meta_description=meta.get("description", ""),
        headings=headings,
        body_text=body_text,
    )

    result.update(
        {
            "title": title,
            "meta_description": meta.get("description", ""),
            "meta_keywords_tag": meta.get("keywords", ""),
            "og_title": meta.get("og:title", ""),
            "og_description": meta.get("og:description", ""),
            "canonical": meta.get("canonical", ""),
            "headings": headings,
            "internal_links": _extract_internal_links(html, url),
            "keywords": keywords,
            "search_intent": _infer_intent(keywords, headings),
            "visible_text_sample": body_text[:1500],
        }
    )

    top_terms = [str(k["term"]) for k in keywords[:5]]
    brand = urlparse(url).netloc.replace("www.", "").split(".")[0]
    search_query = f"{brand} {' '.join(top_terms[:3])} competitors"
    web_ctx = await _web_context(search_query)
    if web_ctx:
        result["web_context"] = web_ctx
        result["web_search_query"] = search_query

    return result


def format_site_intelligence(data: dict) -> str:
    """Human-readable block for LLM agents."""
    if data.get("fetch_error") or data.get("warning"):
        return (
            f"⚠️ Site intelligence limited for {data.get('url')}\n"
            f"- Error: {data.get('fetch_error') or data.get('warning')}\n"
            "- Researcher must infer keywords from URL/domain and scan data only."
        )

    lines = [
        f"Source: {data.get('url')} (HTTP {data.get('http_status', '?')})",
        f"Title: {data.get('title') or '(missing)'}",
        f"Meta description: {data.get('meta_description') or '(missing)'}",
        f"Search intent (inferred): {data.get('search_intent')}",
        "",
        "Auto-extracted keywords (from page content — primary source):",
    ]
    for kw in data.get("keywords") or []:
        lines.append(f"  - {kw['term']} ({kw['type']}, freq {kw['count']})")

    headings = data.get("headings") or []
    if headings:
        lines.append("")
        lines.append("Headings:")
        for h in headings[:12]:
            lines.append(f"  - {h['level']}: {h['text']}")

    links = data.get("internal_links") or []
    if links:
        lines.append("")
        lines.append(f"Internal link sample ({len(links)} paths):")
        lines.append("  " + ", ".join(links[:15]))

    if data.get("web_context"):
        lines.extend(["", "Web context (competitor/SERP signals):", data["web_context"]])

    return "\n".join(lines)