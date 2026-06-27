"""Run Operation Silent Consent demo against production AgentNexus API."""

from __future__ import annotations

import json
import sys
import time
import uuid

import httpx

API_BASE = "https://agentnexus-api.obolla.com"
SKILL_SLUG = "fable5-coding-agent"
POLL_SECONDS = 8
MAX_WAIT_SECONDS = 600

DEMO_TASK = """INCIDENT: AgentNexus Local Agent Bridge — consent timeout UX bug

Stack:
- Cloudflare Worker Durable Object: cloudflare/worker/src/bridge-hub.ts
- Handlers: cloudflare/worker/src/bridge-handlers.ts
- Types: cloudflare/worker/src/bridge-types.ts
- Frontend bridge UI polls GET /api/v1/bridge/consent/pending

Symptom:
When waitForWebConsent() times out (CONSENT_WAIT_MS), the promise resolves null
but the web dashboard never receives consent_resolved — users see a stuck pending
request with no error, no retry, no toast.

Reproduction:
1. Pair bridge device
2. Trigger a write tool that requires consent
3. Wait > CONSENT_WAIT_MS without clicking Allow/Deny
4. UI still shows pending; device gets null silently

Your job (Fable-5 agent pipeline):
1. PLAN — explore files, root cause, numbered fix plan with verify commands
2. IMPLEMENT — TypeScript patches:
   - broadcast consent_expired event on timeout in bridge-hub.ts
   - extend bridge-types.ts if needed
   - minimal React handler snippet for Bridge consent panel (frontend/src/pages/Bridge.tsx)
   - Vitest or node test stub for timeout broadcast behavior
3. REVIEW — security (no secret leak), race conditions, WebSocket cleanup
4. QA — READY only if: event typed, UI handling described, test command included, no placeholders

Constraints:
- No secrets in output
- Full code blocks only (no ... omissions)
- Match existing naming (consent_request, consent_resolved, consent_sync)
- npm run build must pass after changes

Success criteria:
- User sees explicit "consent expired" state within 1s of timeout
- Pending entry removed from DO map
- Device receives deterministic error, not silent null

Final QA section: write verdict summary in Thai (ภาษาไทย)."""


def score_output(final_output: str, intermediate: dict) -> dict:
    text = (final_output or "").lower()
    steps = intermediate.get("expert_skill_steps") or {}
    plan = (steps.get("plan") or "").lower()
    implement = (steps.get("implement") or "").lower()
    review = (steps.get("review") or "").lower()
    qa = (steps.get("qa") or "").lower()
    score = 0
    notes: list[str] = []

    if "bridge-hub" in plan or "bridge_hub" in plan:
        score += 2
        notes.append("+2 plan cites real bridge files")
    else:
        notes.append("0 plan missing bridge file references")

    if "consent_expired" in implement or "consent expired" in implement:
        score += 2
        notes.append("+2 implement adds consent_expired handling")
    else:
        notes.append("0 implement missing consent_expired")

    if "npm" in implement or "vitest" in implement or "pytest" in implement:
        score += 1
        notes.append("+1 verify commands present")

    if "/10" in review and ("p0" in review or "p1" in review):
        score += 2
        notes.append("+2 review has score + severity table")
    else:
        notes.append("0 review weak")

    if "verdict:** ready" in qa or "verdict: ready" in qa or "**ready**" in qa:
        score += 2
        notes.append("+2 QA READY")
    elif "needs_correction" in qa:
        notes.append("0 QA NEEDS_CORRECTION")
    else:
        notes.append("0 QA verdict unclear")

    if "ภาษาไทย" in qa or "พร้อม" in qa or "verdict" in qa:
        score += 1
        notes.append("+1 Thai QA summary")

    return {"score": min(score, 10), "notes": notes, "steps": list(steps.keys())}


def main() -> int:
    email = f"demo-{uuid.uuid4().hex[:8]}@agentnexus.dev"
    password = "DemoPass123!"

    with httpx.Client(base_url=API_BASE, timeout=120.0) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Fable5 Demo"},
        )
        if reg.status_code not in (200, 201):
            print(f"register failed: {reg.status_code} {reg.text}", file=sys.stderr)
            return 1
        print(f"user: {email}")

        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        login.raise_for_status()
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        wallet = client.get("/api/v1/billing/wallet", headers=headers)
        if wallet.status_code == 200:
            print(f"wallet: ${wallet.json().get('balance_usd', '?')}")

        run = client.post(
            f"/api/v1/expert-skills/{SKILL_SLUG}/run",
            headers=headers,
            json={"task_description": DEMO_TASK},
        )
        if run.status_code >= 400:
            print(f"run failed: {run.status_code} {run.text}", file=sys.stderr)
            return 1
        payload = run.json()
        workflow_id = payload["workflow_id"]
        print(f"workflow_id: {workflow_id}")
        print("status: running — polling...")

        deadline = time.time() + MAX_WAIT_SECONDS
        last_status = ""
        while time.time() < deadline:
            time.sleep(POLL_SECONDS)
            status_resp = client.get(f"/api/v1/workflows/{workflow_id}", headers=headers)
            status_resp.raise_for_status()
            data = status_resp.json()
            status = data.get("status", "")
            if status != last_status:
                print(f"  → {status}")
                last_status = status
            if status in ("completed", "failed"):
                result = data
                break
        else:
            print("timeout waiting for workflow", file=sys.stderr)
            return 1

        intermediate = result.get("intermediate_results") or {}
        steps = intermediate.get("expert_skill_steps") or {}
        billing = result.get("billing") or {}

        from pathlib import Path

        out_path = Path(__file__).resolve().parents[2] / ".production" / "fable5-demo-result.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"saved: {out_path}")

        print("\n=== BILLING ===")
        print(json.dumps(billing, indent=2))
        print("\n=== METRICS ===")
        print(f"tokens: {result.get('total_tokens')}")
        print(f"cost_usd: {result.get('total_cost_usd')}")
        print(f"time_sec: {result.get('execution_time_seconds')}")

        scored = score_output(result.get("final_output") or "", intermediate)
        print(f"\n=== DEMO SCORE: {scored['score']}/10 ===")
        for note in scored["notes"]:
            print(f"  {note}")

        for step_id in ("plan", "implement", "review", "qa"):
            body = steps.get(step_id, "")
            print(f"\n{'=' * 20} {step_id.upper()} ({len(body)} chars) {'=' * 20}")
            preview = body[:3500] + ("…" if len(body) > 3500 else "")
            print(preview)

        if result.get("status") == "failed":
            print("\nFAILED:", result.get("error_message"))
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())