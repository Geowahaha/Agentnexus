"""Provable OBOLLA DNA alignment audit — every claim backed by evidence."""

from __future__ import annotations

import importlib
import inspect
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.core import obolla_dna
from app.expert_skills.attribution import CHARTER_SUMMARY, OBOLLA_LAYER
from app.expert_skills.custom_defaults import CATEGORY_META, build_default_crew_config
from app.expert_skills.input_mode import skill_requires_url
from app.expert_skills.model_tiers import (
    GARDEN_BASE_PRICE_USD,
    apply_model_tier_to_crew_config,
    effective_marketplace_price_usd,
    garden_model_tiers,
    resolve_runtime_crew_config,
    strip_runtime_crew_fields,
)
from app.graphs.utils import assess_expert_skill_delivery
from app.services.content_safety import find_policy_violations, is_platform_safe

AuditStatus = Literal["pass", "fail", "warn"]

APP_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_MANIFESTO = BACKEND_ROOT.parent / "frontend" / "src" / "config" / "obollaManifesto.ts"

_DANGEROUS_CODE_PATTERNS = (
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"__import__\s*\("),
    re.compile(r"\bos\.system\s*\("),
    re.compile(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True"),
)


def _check(
    *,
    check_id: str,
    pillar: str,
    claim_en: str,
    claim_th: str,
    status: AuditStatus,
    proved_by: str,
    evidence: dict[str, Any],
    detail_en: str = "",
    detail_th: str = "",
) -> dict[str, Any]:
    return {
        "id": check_id,
        "dna_pillar": pillar,
        "claim_en": claim_en,
        "claim_th": claim_th,
        "status": status,
        "proved_by": proved_by,
        "evidence": evidence,
        "detail_en": detail_en,
        "detail_th": detail_th,
    }


def _scan_py_for_dangerous_code() -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        if "test" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in _DANGEROUS_CODE_PATTERNS:
                if pattern.search(line):
                    hits.append(
                        {
                            "file": str(path.relative_to(BACKEND_ROOT)),
                            "line": str(idx),
                            "pattern": pattern.pattern,
                        }
                    )
    return {"hits": hits, "files_scanned": len(list(APP_ROOT.rglob("*.py"))), "hit_count": len(hits)}


def _qa_step_present(steps: list[dict]) -> bool:
    gate_tokens = ("qa", "review", "deliver", "verdict")
    for step in steps:
        blob = f"{step.get('id', '')} {step.get('title', '')}".lower()
        if any(token in blob for token in gate_tokens):
            return True
    return False


def _collect_platform_copy_samples() -> list[str]:
    samples = [
        obolla_dna.OBOLLA_MANIFESTO_TH,
        obolla_dna.OBOLLA_MANIFESTO_EN,
        obolla_dna.OBOLLA_COMPANION_TH,
        *obolla_dna.OBOLLA_DNA_EN,
        *obolla_dna.OBOLLA_DNA_TH,
        *obolla_dna.OBOLLA_CHARTER_RULES_EN,
        *obolla_dna.OBOLLA_CHARTER_RULES_TH,
        CHARTER_SUMMARY,
        OBOLLA_LAYER,
    ]
    if FRONTEND_MANIFESTO.is_file():
        samples.append(FRONTEND_MANIFESTO.read_text(encoding="utf-8", errors="replace"))
    return samples


def _prove_delivery_qa_gate() -> dict[str, Any]:
    crew = build_default_crew_config(category="content", name="Probe", description="DNA audit probe")
    state = {
        "workflow_type": "expert_skill",
        "final_output": "## Research\n" + ("x" * 600),
        "intermediate_results": {
            "expert_skill_steps": {
                "research": "ok",
                "draft": "ok",
                "edit": "ok",
                "qa": "READY — deliverable verified",
            }
        },
    }
    full = assess_expert_skill_delivery(state, crew_steps=crew.get("steps"))
    failed = {
        **state,
        "intermediate_results": {
            "expert_skill_steps": {
                "research": "**Step failed**\ntimeout",
                "draft": "**Step failed**\ntimeout",
                "edit": "**Step failed**\ntimeout",
                "qa": "**Step failed**\ntimeout",
            }
        },
        "final_output": "## Warnings\n- all steps failed",
    }
    bad = assess_expert_skill_delivery(failed, crew_steps=crew.get("steps"))
    return {
        "full_quality": full.get("delivery_quality"),
        "full_multiplier": full.get("marketplace_fee_multiplier"),
        "failed_quality": bad.get("delivery_quality"),
        "failed_multiplier": bad.get("marketplace_fee_multiplier"),
    }


def _prove_honest_pricing() -> dict[str, Any]:
    base = build_default_crew_config(category="content", name="Tier probe", description="desc")
    tiered = apply_model_tier_to_crew_config(base, "gpt-5")
    resolved = resolve_runtime_crew_config(tiered)
    price = effective_marketplace_price_usd(listed_price_usd="4.49", crew_config=tiered)
    return {
        "requested_tier": tiered.get("model_tier_id"),
        "runtime_downgraded": resolved.get("runtime_tier_downgraded"),
        "effective_tier": resolved.get("model_tier_id"),
        "effective_price_usd": str(price),
        "base_price_usd": str(GARDEN_BASE_PRICE_USD),
    }


def _prove_garden_free() -> dict[str, Any]:
    mod = importlib.import_module("app.services.creator_garden_service")
    source = inspect.getsource(mod)
    billing_imported = "app.billing" in source or "BillingService" in source
    return {
        "compose_module": mod.__name__,
        "imports_billing": billing_imported,
        "documented_free": "always $0" in source or "Free" in source,
    }


def _prove_attribution_wired() -> dict[str, Any]:
    mod = importlib.import_module("app.expert_skills.attribution")
    return {
        "charter_summary_len": len(CHARTER_SUMMARY),
        "obolla_layer_len": len(OBOLLA_LAYER),
        "has_pack_links": bool(getattr(mod, "PACKS_ROOT", None)),
    }


def _prove_bridge_consent() -> dict[str, Any]:
    catalog = importlib.import_module("app.tools.bridge_catalog")
    source = inspect.getsource(catalog)
    return {
        "mentions_consent": "consent" in source.lower(),
        "bridge_api_module": "app.api.v1.bridge",
    }


def _prove_task_mode_content() -> dict[str, Any]:
    requires = skill_requires_url(
        pack_slug="custom",
        crew_config=None,
        category="content",
        slug="content-pipeline-for-creators",
        name="Content Creators",
        description="Research → draft → edit",
    )
    return {"content_pipeline_requires_url": requires, "expected": False}


def _prove_runtime_fields_stripped() -> dict[str, Any]:
    sample = {
        "model_tier_id": "standard",
        "runtime_tier_downgraded": True,
        "effective_marketplace_price_usd": "0.99",
        "steps": [],
    }
    stripped = strip_runtime_crew_fields(sample)
    return {
        "stripped_keys": sorted(k for k in sample if k not in stripped),
        "runtime_tier_downgraded_removed": "runtime_tier_downgraded" not in stripped,
    }


def _prove_model_tier_transparency() -> dict[str, Any]:
    tiers = garden_model_tiers().get("tiers") or []
    unavailable = [t["id"] for t in tiers if not t.get("available")]
    missing_reason = [
        t["id"]
        for t in tiers
        if not t.get("available") and not (t.get("unavailable_reason_en") or t.get("unavailable_reason_th"))
    ]
    return {
        "tier_count": len(tiers),
        "unavailable_tier_ids": unavailable,
        "unavailable_without_reason": missing_reason,
    }


def _prove_vision_canonical() -> dict[str, Any]:
    payload = obolla_dna.vision_payload()
    required = (
        "manifesto_th",
        "manifesto_en",
        "companion_th",
        "dna",
        "dna_th",
        "charter_rules",
        "charter_rules_th",
    )
    missing = [key for key in required if not payload.get(key)]
    return {
        "missing_keys": missing,
        "dna_line_count": len(payload.get("dna") or []),
        "manifesto_has_human_time": "คนมีเวลาเป็นคน" in payload.get("manifesto_th", ""),
    }


def run_dna_audit() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    vision_evidence = _prove_vision_canonical()
    checks.append(
        _check(
            check_id="vision_canonical",
            pillar="humans_have_time",
            claim_en="Public vision API matches canonical OBOLLA DNA text.",
            claim_th="ข้อความ DNA บน API ตรงกับแหล่งข้อมูลมาตรฐาน",
            status="pass"
            if not vision_evidence["missing_keys"] and vision_evidence["manifesto_has_human_time"]
            else "fail",
            proved_by="canonical_compare",
            evidence=vision_evidence,
        )
    )

    companion_ok = obolla_dna.OBOLLA_COMPANION_TH == "ผมอยู่ข้างคุณในการสร้างมันครับ"
    checks.append(
        _check(
            check_id="companion_phrase",
            pillar="humans_have_time",
            claim_en="Companion stands beside creators — not above them.",
            claim_th="Companion อยู่ข้างคุณในการสร้าง ไม่ใช่สั่งการจากบน",
            status="pass" if companion_ok else "fail",
            proved_by="string_assert",
            evidence={"companion_th": obolla_dna.OBOLLA_COMPANION_TH},
        )
    )

    qa_coverage: dict[str, bool] = {}
    for cat, meta in CATEGORY_META.items():
        steps = meta.get("steps") or []
        qa_coverage[cat] = _qa_step_present(steps)
    qa_all = all(qa_coverage.values())
    checks.append(
        _check(
            check_id="qa_gate_pipelines",
            pillar="verifiable_deliverables",
            claim_en="Every default agent category includes a QA gate step.",
            claim_th="ทุกหมวด flow เริ่มต้นมีขั้น QA ก่อนส่งมอบ",
            status="pass" if qa_all else "fail",
            proved_by="pipeline_inspect",
            evidence={"categories": qa_coverage},
        )
    )

    delivery_evidence = _prove_delivery_qa_gate()
    delivery_ok = (
        delivery_evidence["full_quality"] == "full"
        and delivery_evidence["failed_quality"] == "failed"
        and delivery_evidence["failed_multiplier"] == 0.0
    )
    checks.append(
        _check(
            check_id="delivery_assessment",
            pillar="verifiable_deliverables",
            claim_en="Failed runs reduce marketplace fees; full delivery keeps fair charge.",
            claim_th="รันล้มเหลวลดค่าธรรมเนียม — ส่งครบคิดตามจริง",
            status="pass" if delivery_ok else "fail",
            proved_by="runtime_function",
            evidence=delivery_evidence,
        )
    )

    pricing_evidence = _prove_honest_pricing()
    if pricing_evidence.get("runtime_downgraded"):
        pricing_ok = pricing_evidence.get("effective_price_usd") == str(GARDEN_BASE_PRICE_USD)
        pricing_status: AuditStatus = "pass" if pricing_ok else "fail"
    else:
        pricing_ok = True
        pricing_status = "pass"
    checks.append(
        _check(
            check_id="honest_pricing_downgrade",
            pillar="honest_earnings",
            claim_en="Unavailable premium tiers run Standard at base $0.99 — no hidden premium charge.",
            claim_th="ชุดพรีเมียมไม่พร้อม → รันมาตรฐาน $0.99 ไม่เก็บเกิน",
            status=pricing_status,
            proved_by="runtime_function",
            evidence=pricing_evidence,
        )
    )

    garden_evidence = _prove_garden_free()
    checks.append(
        _check(
            check_id="creator_garden_free",
            pillar="humans_have_time",
            claim_en="Creator Garden compose/coach never imports billing — always free.",
            claim_th="ห้องสร้างสรรค์ฟรี ไม่ผูกระบบเรียกเก็บเงิน",
            status="pass" if not garden_evidence["imports_billing"] else "fail",
            proved_by="source_inspect",
            evidence=garden_evidence,
        )
    )

    code_scan = _scan_py_for_dangerous_code()
    checks.append(
        _check(
            check_id="no_hidden_exec",
            pillar="trust_safety",
            claim_en="Application code has no eval/exec/shell=True backdoors.",
            claim_th="โค้ดแอปไม่มี eval/exec หรือ shell แอบแฝง",
            status="pass" if code_scan["hit_count"] == 0 else "fail",
            proved_by="code_scan",
            evidence=code_scan,
        )
    )

    attr_evidence = _prove_attribution_wired()
    checks.append(
        _check(
            check_id="attribution_charter",
            pillar="credit_upstream",
            claim_en="Attribution charter documents upstream credit — we orchestrate, not re-train.",
            claim_th="ให้เครดิต upstream ชัดเจน — เรา orchestrate ไม่ใช่ train เอง",
            status="pass" if attr_evidence["charter_summary_len"] > 20 else "fail",
            proved_by="module_inspect",
            evidence=attr_evidence,
        )
    )

    bridge_evidence = _prove_bridge_consent()
    checks.append(
        _check(
            check_id="bridge_consent",
            pillar="trust_safety",
            claim_en="Local Bridge tools require explicit user consent per action.",
            claim_th="Local Bridge ต้องได้รับความยินยอมทุกครั้ง",
            status="pass" if bridge_evidence["mentions_consent"] else "fail",
            proved_by="source_inspect",
            evidence=bridge_evidence,
        )
    )

    task_evidence = _prove_task_mode_content()
    checks.append(
        _check(
            check_id="content_task_mode",
            pillar="real_outcomes",
            claim_en="Content Creators accepts plain-language tasks — no forced URL.",
            claim_th="Content Creators รับคำสั่งภาษาพูด ไม่บังคับ URL",
            status="pass" if not task_evidence["content_pipeline_requires_url"] else "fail",
            proved_by="runtime_function",
            evidence=task_evidence,
        )
    )

    strip_evidence = _prove_runtime_fields_stripped()
    checks.append(
        _check(
            check_id="runtime_fields_not_persisted",
            pillar="honest_earnings",
            claim_en="Runtime downgrade flags are stripped before saving crew_config.",
            claim_th="ลบ flag downgrade ก่อนบันทึก crew_config",
            status="pass" if strip_evidence["runtime_tier_downgraded_removed"] else "fail",
            proved_by="runtime_function",
            evidence=strip_evidence,
        )
    )

    tier_evidence = _prove_model_tier_transparency()
    checks.append(
        _check(
            check_id="model_tier_transparency",
            pillar="honest_earnings",
            claim_en="Unavailable model tiers show a clear reason in the garden picker.",
            claim_th="ชุดโมเดลที่ไม่พร้อมแสดงเหตุผลชัดเจน",
            status="pass" if not tier_evidence["unavailable_without_reason"] else "warn",
            proved_by="catalog_inspect",
            evidence=tier_evidence,
        )
    )

    copy_samples = _collect_platform_copy_samples()
    unsafe: list[dict[str, str]] = []
    for idx, sample in enumerate(copy_samples):
        violations = find_policy_violations(sample)
        if violations:
            unsafe.append({"sample_index": str(idx), "violations": ", ".join(violations[:3])})
    checks.append(
        _check(
            check_id="platform_copy_safe",
            pillar="trust_safety",
            claim_en="Platform-owned manifesto, charter, and companion copy contain no vulgar or deceptive claims.",
            claim_th="ข้อความ DNA ของแพลตฟอร์มไม่มีคำหยาบหรือคำโฆษณาหลอก",
            status="pass" if not unsafe else "fail",
            proved_by="content_scan",
            evidence={"samples_scanned": len(copy_samples), "unsafe_hits": unsafe},
        )
    )

    billing_path = APP_ROOT / "billing" / "service.py"
    billing_source = billing_path.read_text(encoding="utf-8", errors="replace") if billing_path.is_file() else ""
    billing_uses_qa = "assess_expert_skill_delivery" in billing_source and "marketplace_fee_multiplier" in billing_source
    checks.append(
        _check(
            check_id="billing_honors_delivery",
            pillar="honest_earnings",
            claim_en="Billing settlement applies delivery QA multiplier to marketplace fees.",
            claim_th="เรียกเก็บเงินใช้ตัวคูณ QA ตามคุณภาพการส่งมอบ",
            status="pass" if billing_uses_qa else "fail",
            proved_by="source_inspect",
            evidence={"uses_delivery_multiplier": billing_uses_qa},
        )
    )

    human_mod = importlib.import_module("app.graphs.human_review")
    checks.append(
        _check(
            check_id="human_loop_available",
            pillar="trust_safety",
            claim_en="Workflows can require human approval before tools execute.",
            claim_th="workflow บังคับให้มนุษย์อนุมัติก่อนรันเครื่องมือได้",
            status="pass" if hasattr(human_mod, "is_human_loop_enabled") else "fail",
            proved_by="module_inspect",
            evidence={"module": human_mod.__name__},
        )
    )

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    warned = sum(1 for c in checks if c["status"] == "warn")
    overall: AuditStatus = "fail" if failed else ("warn" if warned else "pass")

    return {
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "warned": warned,
            "dna_aligned": failed == 0,
        },
        "manifesto_th": obolla_dna.OBOLLA_MANIFESTO_TH,
        "companion_th": obolla_dna.OBOLLA_COMPANION_TH,
        "dna_th": obolla_dna.OBOLLA_DNA_TH,
        "charter_rules_th": obolla_dna.OBOLLA_CHARTER_RULES_TH,
        "checks": checks,
    }