"""Extract window.IJ_values from PSI HTML and search for lighthouse metrics."""

import json
import re
import sys
from pathlib import Path

html = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
m = re.search(r"window\.IJ_values\s*=\s*(\[.+?\]);\s*</script>", html, re.DOTALL)
if not m:
    print("IJ_values not found")
    sys.exit(1)

raw = m.group(1)
# PSI uses JS array literal; try json after normalizing
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    # fallback: search raw string for metrics
    data = None

print("IJ_values parsed:", data is not None)
text = raw if data is None else json.dumps(data)

needles = [
    "largest-contentful-paint",
    "first-contentful-paint",
    "cumulative-layout-shift",
    "total-blocking-time",
    "speed-index",
    "interaction-to-next-paint",
    "performance",
    "displayValue",
    "cpefoundry",
    "LCP",
    "CLS",
]
for n in needles:
    if n.lower() in text.lower():
        print(f"  contains: {n}")

if data is not None:

    def walk(obj, path=""):
        if isinstance(obj, dict):
            if "lighthouseResult" in obj or "categories" in obj:
                print("FOUND lighthouse at", path)
                if "categories" in obj:
                    for k, v in obj["categories"].items():
                        if isinstance(v, dict) and "score" in v:
                            print(f"  {k}: {v['score']}")
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if i > 200:
                    break
                walk(v, f"{path}[{i}]")

    walk(data)

# Brute search for score-like numbers near performance keyword
for pat in [
    r"performance.{0,200}?score.{0,20}?([\d.]+)",
    r"largest-contentful-paint.{0,300}?displayValue.{0,20}?([^\\]+)",
]:
    hits = re.findall(pat, text, re.IGNORECASE)
    if hits:
        print(f"pattern {pat[:40]}... -> {hits[:3]}")