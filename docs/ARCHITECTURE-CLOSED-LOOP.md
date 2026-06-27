# Architecture: AIBotAuth + OBOLLA Closed Loop + Data Moat

**Date**: 2026-06-26
**Principles**: Data Moat #1. Production-grade only (per .production/PRODUCTION-RULES.md and Agents.md). Separate public brands but unified intelligence plane. MCP as lingua franca. Instrument every meaningful event. No mock data.

## High-Level Topology (Real Today + Target)

```
Public Surfaces
├── https://aibotauth.com          (Agent-Ready Certification)
│   ├── / (scan UI + proof viewer)
│   ├── /api/mcp (MCP Server exposing scan + related)
│   ├── /api/proof (partner proof creation for OBOLLA etc.)
│   └── Web Bot Auth signed crawler (Ed25519, RFC9421)
│
└── https://obolla.com             (AI Garden / Marketplace + execution)
    ├── SPA on Cloudflare Worker (edge)
    ├── /expert-skills/* , workflows, creator garden, agent-ready
    └── API proxy in Worker → tunnel → VPS backend

Shared/Backend Plane (VPS 43.128.75.149 — 24/7 only)
├── FastAPI (agentnexus-api docker)
├── PostgreSQL (core + moat events)
├── MCP client (HttpMcpClient) for calling external MCPs incl. AIBotAuth
├── LangGraph execution (expert_skill graphs)
├── AgentReadyOrchestrator + IsitagentreadyClient + proof client
└── Billing / attribution / wallet

Data Moat Layer (NEW, to be built on top)
├── visibility_events (scans + proofs + deltas)
├── skill_execution_events (runs + context + outcomes + links)
├── attribution_events (dynamic linkage + earnings correlation)
└── (future) behavioral_aggregates, benchmarks

Interconnect Primitives (Already Working, Strengthen)
- MCP: AIBotAuth registered as external MCP server; skills invoke "mcp.aibotauth.scan"
- Proof bridge: OBOLLA calls /api/proof on AIBotAuth with key → returns share_id + embed
- Showcases + attribution charters link live examples
- Agent-ready flows produce proofs
```

## Data Moat Schema Targets (Long-term PM Priority — 3-5yr Durable Asset)
1. `visibility_events` — supporting raw signals + proofs (provenance layer).
2. `skill_execution_events` — cost and high-level execution.
3. **`agent_behavior_traces`** (PM core durable moat table, v1.1+ with formal schema):
   - Uses proprietary `AgentBehaviorFingerprint` Pydantic schema (typed events: MCPCallEvent, LLMReasoningEvent, DecisionEvent, etc.).
   - Cryptographically signed (Ed25519) for tamper-evidence and unique ownership.
   - Explicit pre/post + causal_lift + provenance graphs.
   - `fingerprint_version` for long-term evolution (see model for v-plan: normalize revenue, add MCP).
   - Compounding engine: feeds SkillEfficacyProfiles with proprietary RevenueCausalFidelity + ClosedLoopCorrelation + UniqueLoopMultiplier + active proprietary_validation_correlation (PM 2-area push executed: 1. Early Revenue Execution — use logged sales data (pipeline) to do real sales: log_revenue_sale creates BillingTransaction+CreatorEarning, records billing_id/earning_id/results/status=closed. 2. Proprietary Validation — clear plan + actively collect via outcomes + run_batch_validation_stats (avg_corr, variance, high>0.6, sales_outcomes_count) after each real sale from logs. Dashboard pipeline + buttons drive both. Data now proving in DB.).
   - Replication barrier: Requires signed real-web visibility (AIBotAuth Ed25519/Web Bot Auth) + executed high-signal skills + full causal trajectories at scale. Generic loggers and simulators cannot match ecological validity + provenance.

This structure is our IP. Competitors can log generic events; they cannot cheaply create equivalent causally-linked, cryptographically-tied fingerprints without our closed loop.

Longitudinal + compounding queries: "For ecom sites with weak llms.txt, which skill sequences produce >15% lift on average, with statistical significance from our signed scans?"

## Closed Loop Flows (Instrumented)
Flow A: Visibility → Action
1. User scans on AIBotAuth or triggers via OBOLLA skill ("ai-visibility-2026", "fix-bot...", "agent-ready-auto-fix").
2. Capture full visibility_event + create proof.
3. Skill graph may recommend / invoke fix or other skills.
4. Post-run: re-scan trigger (optional) → new visibility_event + delta recorded.

Flow B: Action → Attribution → Intelligence
1. Marketplace workflow executes (LangGraph).
2. At key steps (esp. scan, post-QA, final): log execution_event.
3. On billing charge: attempt auto-link to recent visibility_events for the URLs.
4. On buyer review or creator earning: enrich attribution.
5. Aggregate feeds:
   - Creator dashboard: skill performance + attribution.
   - Site owner view (future): agent activity on my certified pages.
   - Platform benchmarks.

## Platform Separation vs Unity
- AIBotAuth brand = pure trust/certification surface. Public proofs, bot identity.
- OBOLLA brand = garden/community/marketplace/execution. Thai-first copy, creators, buyers.
- Shared backend data plane + MCP for loose coupling.
- Config: `aibotauth_base_url`, `aibotauth_mcp_url`, `aibotauth_mcp_api_key`.
- Future: AIBotAuth could expose its own minimal API surface or be partially implemented via shared services.

## Technical Stack & Constraints
- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL (VPS).
- Execution: LangGraph + MCP HTTP JSON-RPC client.
- Frontend: Vite + React/TS on CF Worker.
- Auth: existing + Google.
- Deploy: `scripts/deploy-obolla.ps1` (edge), `deploy-vps-production.ps1` (backend). Health must report backend_reachable true.
- No dev machine as prod.
- Instrument without breaking existing runs (additive logging, best-effort).

## MCP Extensions (for moat)
- Keep AIBotAuth as authoritative MCP for scans.
- Consider OBOLLA MCP server exposing "recommended skills for url" or "get attribution summary" (auth-gated) — future.

## Instrumentation Points (Build Now) — PM Phase 1 Upgrades
1. `aibotauth_proof_client.py` — after successful proof creation, persist visibility_event (with raw details).
2. `graphs/expert_skill.py` + workflow — full `expert_skill_steps`, MCP results, and behavioral_trace captured.
3. Workflow/billing paths — rich execution + `record_behavioral_trace` + lift hooks.
4. `moat_service.py` — `record_behavioral_trace`, `compute_and_store_lift` (pre/post delta).
5. `/moat/intelligence` — structured signals + derived lift for Revenue Intelligence product (creator & site owner value).

PM Note: Generic logging rejected. We require step-level traces + causal measurement + ownership of signed artifacts.

## Security & Privacy (Defense in Depth for Revenue Data)
- Ed25519 signing (canonical JSON + SHA256) for all revenue_attribution in fingerprints and profiles.
- Verification on API reads.
- Least privilege in queries; data minimization (only workflow-linked revenue).
- Audit via existing logging + signature timestamps.
- Future: at-rest encryption for sensitive fields, rate limits on revenue endpoints.
- Revenue data is never exposed without signature verification.

## Evolution Path
Phase 0 (Now): Basic event tables + logging at proof + scan steps. Read APIs for internal use.
Phase 1: Dynamic attribution enrichment, simple Intelligence tab in CreatorDashboard.
Phase 2: Public benchmarks, Revenue Intelligence product, agent-facing APIs.
Phase 3: Predictive models on top of moat (e.g. "expected lift from skill X on stack Y").

## Revenue Execution + Proprietary Validation Schema Evolution (v1.1 → v2+)
Current (executed in this cycle):
- moat_skill_efficacy.profile_data holds:
  - validated_revenue_outcomes: list[{amount_usd, timestamp, billing_recorded, billing_id, earning_id, prop_correlation_at_sale}]
  - logged_sales_pipeline: {pending: [...], executed: [...] }  (durable logged data source)
  - validation_history
- BillingTransactionORM + CreatorEarningORM created on /revenue-sale/log from logged items (with resolved skill owner_id when possible).
- run_batch_validation_stats produces revenue_correlation_estimate (pearson-like from real prop<->$ pairs) + variance + counts.

Long-term (3-5yr defensibility):
- v1.2: Dedicated revenue_execution_log table (id, skill_slug, logged_id, amount, billing_id, earning_id, prop_score_at_time, signature).
- Stronger cryptographic provenance on every outcome row.
- Schema version in profile_data + migration path (alembic for moat tables).
- Batch jobs to compute full rolling Pearson + confidence intervals on >N sales.
- Link execution traces directly to revenue rows for step-level causal revenue fidelity.
- MCP tool exposure of safe aggregated validation stats for agent use (without raw revenue).

This compounds: more executed sales from logged → richer outcomes → higher correlation proof → premium pricing + moat strength.
All revenue data Ed25519 signed + minimized + audited.

## Non-Goals (Ruthless Filter)
- Rebuild AIBotAuth scanner inside this monorepo if it is successfully operating at domain.
- General-purpose agent runtime (focus on marketplace + visibility intelligence).
- Outcome-based payouts until attribution is robust and consented.

This architecture makes the Data Moat real and central.
