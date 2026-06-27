"""Run OBOLLA DNA audit — exit 0 when all checks pass, 1 on failure."""

from __future__ import annotations

import json
import sys

from app.services.dna_audit_service import run_dna_audit


def main() -> int:
    report = run_dna_audit()
    summary = report["summary"]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if summary["failed"] > 0:
        print(f"\nDNA audit FAILED: {summary['failed']} check(s) failed.", file=sys.stderr)
        return 1
    if summary["warned"] > 0:
        print(f"\nDNA audit OK with warnings: {summary['warned']}.", file=sys.stderr)
    else:
        print(f"\nDNA audit PASSED: {summary['passed']}/{summary['total']} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())