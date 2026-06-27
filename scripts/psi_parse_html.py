"""Parse embedded data from PageSpeed Insights HTML snapshot."""

import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("psi_page.html")
html = path.read_text(encoding="utf-8", errors="ignore")

print(f"HTML size: {len(html):,} bytes")

# PSI often embeds lighthouseResult in escaped JSON
for label, pattern in [
    ("performance score", r'"performance"[^}]*"score"\s*:\s*([\d.]+)'),
    ("accessibility score", r'"accessibility"[^}]*"score"\s*:\s*([\d.]+)'),
    ("best-practices score", r'"best-practices"[^}]*"score"\s*:\s*([\d.]+)'),
    ("seo score", r'"seo"[^}]*"score"\s*:\s*([\d.]+)'),
    ("LCP", r'largest-contentful-paint[^}]*"displayValue"\s*:\s*"([^"]+)"'),
    ("FCP", r'first-contentful-paint[^}]*"displayValue"\s*:\s*"([^"]+)"'),
    ("TBT", r'total-blocking-time[^}]*"displayValue"\s*:\s*"([^"]+)"'),
    ("CLS", r'cumulative-layout-shift[^}]*"displayValue"\s*:\s*"([^"]+)"'),
    ("Speed Index", r'speed-index[^}]*"displayValue"\s*:\s*"([^"]+)"'),
    ("INP", r'interaction-to-next-paint[^}]*"displayValue"\s*:\s*"([^"]+)"'),
]:
    m = re.search(pattern, html)
    print(f"{label}: {m.group(1) if m else 'not found'}")

# Try to find lighthouseResult JSON blob
for marker in ['"lighthouseResult"', '\\"lighthouseResult\\"']:
    idx = html.find(marker)
    if idx != -1:
        print(f"\nFound {marker} at offset {idx}")
        snippet = html[idx : idx + 200]
        print(snippet[:200])
        break

# Report date from page
date_m = re.search(r"Report from ([^<]+)", html)
if date_m:
    print(f"\nReport date: {date_m.group(1).strip()}")

crux = "does not have sufficient real-world speed data" in html
print(f"\nCrUX field data: {'No Data' if crux else 'Available'}")