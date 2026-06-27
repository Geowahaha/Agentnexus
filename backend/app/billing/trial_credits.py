"""Trial / demo credit copy and billing metadata helpers."""

from __future__ import annotations

from decimal import Decimal

TRIAL_NOTICE_TH = "การทดลองใช้ — เจ้าของ agent ไม่ได้รับเงินจริง"
TRIAL_NOTICE_EN = "Trial usage — agent owners receive no real payout"


def signup_bonus_description(amount: Decimal) -> str:
    return (
        f"เครดิตทดลองใช้ ${amount:.2f} — แรกเข้า "
        f"(ใช้ซื้อได้ทุกอย่าง · {TRIAL_NOTICE_TH})"
    )


def demo_topup_description(amount: Decimal) -> str:
    return f"เครดิตทดลองใช้ ${amount:.2f} — demo ({TRIAL_NOTICE_TH})"


def workflow_charge_description(
    workflow_id: str,
    *,
    trial_spend: Decimal,
    paid_spend: Decimal,
) -> str:
    if paid_spend <= 0:
        return f"ทดลองใช้ — Workflow {workflow_id} · {TRIAL_NOTICE_TH}"
    if trial_spend <= 0:
        return f"Workflow {workflow_id} — paid credits (creator payout eligible)"
    return (
        f"Workflow {workflow_id} — ทดลอง ${trial_spend:.4f} + จ่ายจริง ${paid_spend:.4f} · "
        f"ส่วนทดลอง: {TRIAL_NOTICE_TH}"
    )


def build_billing_meta(
    *,
    trial_spend: Decimal,
    paid_spend: Decimal,
    creator_payout_eligible: bool,
) -> dict:
    if trial_spend > 0 and paid_spend <= 0:
        funding = "trial"
    elif paid_spend > 0 and trial_spend <= 0:
        funding = "paid"
    else:
        funding = "mixed"
    return {
        "_billing_meta": True,
        "funding": funding,
        "trial_amount_usd": str(trial_spend),
        "paid_amount_usd": str(paid_spend),
        "creator_payout_eligible": creator_payout_eligible,
        "trial_notice": TRIAL_NOTICE_TH if trial_spend > 0 else None,
        "trial_notice_en": TRIAL_NOTICE_EN if trial_spend > 0 else None,
    }


def split_agent_charges(agent_charges: list[dict]) -> tuple[list[dict], dict | None]:
    items: list[dict] = []
    meta: dict | None = None
    for item in agent_charges or []:
        if item.get("_billing_meta"):
            meta = item
        else:
            items.append(item)
    return items, meta