from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timezone

_IPV4_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


def normalize_gateway_ip(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise ValueError("IP address required")
    if "/" in text:
        network = ipaddress.ip_network(text, strict=False)
        if network.num_addresses > 1:
            raise ValueError("Use single host IP (/32), not a subnet range")
        return str(network.network_address)
    if _IPV4_RE.match(text):
        parts = [int(p) for p in text.split(".")]
        if any(p > 255 for p in parts):
            raise ValueError("Invalid IPv4 address")
        return text
    try:
        return str(ipaddress.ip_address(text))
    except ValueError as exc:
        raise ValueError("Invalid IP address") from exc


def gateway_ip_records(entries: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    seen: set[str] = set()
    out: list[dict] = []
    for item in entries:
        ip = normalize_gateway_ip(str(item.get("ip") or ""))
        if ip in seen:
            continue
        seen.add(ip)
        out.append(
            {
                "ip": ip,
                "label": str(item.get("label") or "IoT Gateway").strip()[:80],
                "registered_at": item.get("registered_at") or now,
            }
        )
    return out