"""Creator price ceiling — initial OBOLLA suggestion is the maximum; lowering allowed."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi import HTTPException


def parse_price(value: str | int | float | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if amount < 0:
        return None
    return amount.quantize(Decimal("0.01"))


def price_ceiling_from_crew(crew_config: dict | None) -> Decimal | None:
    if not isinstance(crew_config, dict):
        return None
    return parse_price(crew_config.get("pricing_ceiling_usd"))


def merge_crew_preserve_ceiling(
    existing: dict | None,
    patch: dict | None,
    *,
    proposed_ceiling: Decimal | None = None,
) -> dict:
    """Merge crew_config; pricing_ceiling_usd never increases after first set."""
    merged = dict(existing or {})
    if patch:
        merged.update(patch)
    current = price_ceiling_from_crew(merged)
    if current is not None:
        merged["pricing_ceiling_usd"] = str(current)
        return merged
    if proposed_ceiling is not None:
        merged["pricing_ceiling_usd"] = str(proposed_ceiling)
    return merged


def enforce_price_ceiling(
    *,
    crew_config: dict | None,
    new_price: str | int | float | Decimal,
    locale: str = "en",
) -> None:
    ceiling = price_ceiling_from_crew(crew_config)
    price = parse_price(new_price)
    if ceiling is None or price is None:
        return
    if price > ceiling:
        if locale.startswith("th"):
            detail = (
                f"ราคาสูงสุดที่ตั้งครั้งแรกคือ ${ceiling} — ลดได้ แต่เพิ่มเกินไม่ได้ "
                "เพื่อให้แข่งกันด้วยคุณค่า ไม่ใช่แค่ตั้งราคาสูง"
            )
        else:
            detail = (
                f"Initial price ceiling is ${ceiling} — you may lower it, not raise above "
                "the first OBOLLA suggestion."
            )
        raise HTTPException(status_code=400, detail=detail)