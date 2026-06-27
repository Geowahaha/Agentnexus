"""Unit tests for DNA audit and content safety."""

from app.services.content_safety import find_policy_violations, is_platform_safe
from app.services.dna_audit_service import run_dna_audit


def test_content_safety_clean_manifesto() -> None:
    assert is_platform_safe("เอไอทำงานหนัก — คนมีเวลาเป็นคน")
    assert not is_platform_safe("this is fucking bad")


def test_dna_audit_passes() -> None:
    report = run_dna_audit()
    assert report["summary"]["total"] >= 10
    assert report["summary"]["failed"] == 0, report["checks"]
    assert report["overall_status"] in {"pass", "warn"}
    assert "คนมีเวลาเป็นคน" in report["manifesto_th"]
    ids = {c["id"] for c in report["checks"]}
    for required in (
        "qa_gate_pipelines",
        "delivery_assessment",
        "honest_pricing_downgrade",
        "creator_garden_free",
        "no_hidden_exec",
        "platform_copy_safe",
        "companion_phrase",
    ):
        assert required in ids


if __name__ == "__main__":
    test_content_safety_clean_manifesto()
    test_dna_audit_passes()
    print("dna audit tests passed")