"""Platform operator accounts used for OBOLLA QA — labeled on bills as Platform tested."""

from __future__ import annotations

from decimal import Decimal

from app.core.config import settings

PLATFORM_TEST_NOTICE_TH = (
    "ทดสอบโดยทีมแพลตฟอร์ม OBOLLA (Platform tested) — เจ้าของ agent ไม่ได้รับเงินจริง"
)
PLATFORM_TEST_NOTICE_EN = (
    "OBOLLA platform QA (Platform tested) — agent owners receive no real payout"
)


def platform_admin_emails() -> frozenset[str]:
    raw = settings.platform_admin_emails or ""
    return frozenset(part.strip().lower() for part in raw.split(",") if part.strip())


def is_platform_admin_user(*, email: str, role: str) -> bool:
    if role == "admin":
        return True
    return email.strip().lower() in platform_admin_emails()


def platform_test_charge_description(workflow_id: str) -> str:
    return f"Platform tested — Workflow {workflow_id} · {PLATFORM_TEST_NOTICE_TH}"


def build_platform_test_billing_meta(
    *,
    trial_spend: Decimal,
    paid_spend: Decimal,
) -> dict:
    return {
        "_billing_meta": True,
        "funding": "platform_test",
        "trial_amount_usd": str(trial_spend),
        "paid_amount_usd": str(paid_spend),
        "creator_payout_eligible": False,
        "platform_tested": True,
        "trial_notice": None,
        "trial_notice_en": None,
        "platform_notice": PLATFORM_TEST_NOTICE_TH,
        "platform_notice_en": PLATFORM_TEST_NOTICE_EN,
    }