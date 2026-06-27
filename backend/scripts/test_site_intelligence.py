"""Tests for automatic keyword extraction from HTML."""

import asyncio
import sys

from app.expert_skills.site_intelligence import (
    _extract_keywords_from_sources,
    _parse_meta_tags,
    _strip_tags,
    format_site_intelligence,
    gather_site_intelligence,
)

SAMPLE_HTML = """
<html><head>
<title>CPE Foundry - Cast Iron Products</title>
<meta name="description" content="Leading cast iron foundry and iron casting services.">
</head><body>
<h1>Cast Iron Foundry Services</h1>
<h2>Iron Casting Solutions</h2>
<p>We provide cast iron products and foundry supplies for industrial clients.</p>
<p>Our foundry specializes in iron casting and custom cast iron components.</p>
</body></html>
"""


def test_strip_and_meta() -> None:
    assert "Cast Iron" in _strip_tags("<h1>Cast Iron</h1>")
    meta = _parse_meta_tags(SAMPLE_HTML)
    assert "cast iron foundry" in meta.get("description", "").lower()


def test_keyword_extraction() -> None:
    kws = _extract_keywords_from_sources(
        title="CPE Foundry - Cast Iron Products",
        meta_description="Leading cast iron foundry and iron casting services.",
        headings=[{"level": "h1", "text": "Cast Iron Foundry Services"}],
        body_text=_strip_tags(SAMPLE_HTML),
    )
    terms = {str(k["term"]) for k in kws}
    assert "foundry" in terms or "cast" in terms or "casting" in terms or "iron" in terms


def test_format_without_fetch() -> None:
    out = format_site_intelligence({"url": "https://x.com", "fetch_error": "HTTP 403"})
    assert "limited" in out.lower()


async def test_live_fetch_optional() -> None:
    if "--live" not in sys.argv:
        return
    data = await gather_site_intelligence("https://www.cpefoundry.com")
    print(format_site_intelligence(data))
    assert data.get("keywords") or data.get("fetch_error")


def main() -> None:
    test_strip_and_meta()
    test_keyword_extraction()
    test_format_without_fetch()
    asyncio.run(test_live_fetch_optional())
    print("test_site_intelligence: OK")


if __name__ == "__main__":
    main()