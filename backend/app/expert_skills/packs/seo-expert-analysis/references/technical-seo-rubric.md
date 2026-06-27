# Technical SEO Rubric

## Crawlability & indexability (/10)
- robots.txt valid, not blocking key paths
- XML sitemap present and referenced
- Canonical tags consistent (no chains, no conflicts)
- noindex/nofollow used correctly
- HTTPS everywhere, no mixed content
- www vs apex consistency (no 522/redirect loops)
- Internal links crawlable (not `javascript:void` only)

## Site architecture (/8)
- URL structure logical, lowercase, hyphenated
- Depth ≤3 clicks to money pages
- Pagination/facets handled (canonical or noindex)
- Hreflang if multi-language

## Performance signals (/7)
- LCP < 2.5s (mobile) = pass; 2.5–4s = warn; >4s = fail
- CLS < 0.1 = pass
- TBT < 200ms = pass; >600ms = fail
- Render-blocking CSS/JS in head
- Image optimization (WebP/AVIF, dimensions, lazy below fold)

## Schema & structured data (/5)
- Organization/WebSite or LocalBusiness JSON-LD on homepage
- Valid JSON (no syntax errors)
- Matches visible NAP/entity
- BreadcrumbList on deep pages where useful
- No fake schema (reviews, products not on page)

## P0 triggers (auto-escalate)
- HTTP 4xx/5xx on homepage
- robots.txt blocks entire site
- Missing mobile viewport
- LCP > 10s on mobile lab data
- No HTTPS