"""Smoke test: partner proof badge creation."""
import asyncio
import json
import sys

from app.services.aibotauth_proof_client import create_proof_from_scan


async def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://successcasting.com"
    scan = {
        "url": url if url.endswith("/") else f"{url}/",
        "overall": 88,
        "grade": "B",
        "categories": [{"name": "Technical SEO", "score": 100, "grade": "A"}],
        "summary": "Test proof from OBOLLA partner client.",
    }
    proof = await create_proof_from_scan(url, scan, lang="en")
    print(json.dumps(proof, indent=2))
    return 0 if proof and proof.get("proof_url") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))