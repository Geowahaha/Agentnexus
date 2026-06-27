"""Fetch PageSpeed Insights data via public API."""

import json
import sys
import urllib.parse
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.cpefoundry.com"
STRATEGY = sys.argv[2] if len(sys.argv) > 2 else "mobile"

params = urllib.parse.urlencode(
    {
        "url": URL,
        "strategy": STRATEGY,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    },
    doseq=True,
)
api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?{params}"

with urllib.request.urlopen(api, timeout=120) as resp:
    data = json.load(resp)

lh = data.get("lighthouseResult", {})
cats = lh.get("categories", {})
audits = lh.get("audits", {})

print(f"Analyzed: {data.get('id')}")
print(f"Strategy: {STRATEGY}")
print()
print("=== Category scores ===")
for name, cat in cats.items():
    score = cat.get("score")
    if score is not None:
        print(f"  {name}: {score * 100:.0f}")

print()
print("=== Core metrics ===")
metrics = [
    "first-contentful-paint",
    "largest-contentful-paint",
    "total-blocking-time",
    "cumulative-layout-shift",
    "speed-index",
    "interaction-to-next-paint",
]
for mid in metrics:
    a = audits.get(mid, {})
    if a.get("displayValue"):
        print(f"  {mid}: {a['displayValue']}")

print()
print("=== Top opportunities ===")
opps = []
for aid, a in audits.items():
    details = a.get("details") or {}
    if details.get("type") != "opportunity":
        continue
    score = a.get("score")
    if score is None or score >= 1:
        continue
    opps.append((a.get("numericValue") or 0, aid, a.get("title"), a.get("displayValue")))
opps.sort(reverse=True)
for _, aid, title, disp in opps[:10]:
    print(f"  - {title}: {disp or '—'}")

crux = data.get("loadingExperience", {})
if crux:
    print()
    print("=== CrUX (field data) ===")
    print(f"  overall_category: {crux.get('overall_category', 'N/A')}")