# AIBotAuth + OBOLLA: Closed-Loop Revenue Intelligence for the Agentic Web

**Status**: Founder-level vision (2026-06). Living document. Updated with rigorous challenge.

## Executive Vision
Build **AIBotAuth.com** and **OBOLLA.com** as two tightly interconnected platforms forming a defensible, high-potential startup:

- **AIBotAuth.com** — The authoritative **Agent-Ready Certification** authority. Cryptographically verifiable (Ed25519 + RFC 9421 Web Bot Auth), multi-crawler scans that prove a site is legible, citable, and actionable by autonomous agents. Produces public shareable proofs + embeds.

- **OBOLLA.com** ("AI Garden") — The trusted **marketplace and execution layer** for expert agent skills, MCP tools, and agent flows. Creators publish production skills. Agents and humans discover, compose, purchase, and run them.

**The product is the Closed Loop + the durable, compounding Data Moat it generates (3-5+ year horizon).**

Core promise (PM long-term): We own the highest-fidelity, causally-linked, cryptographically-signed dataset of real agent behaviors and outcomes on the web. Pre/post visibility states (signed via AIBotAuth Web Bot Auth + Ed25519) are directly tied to executed skills through proprietary structured Fingerprints (formal Pydantic schema with typed events, provenance signatures). 

This is expensive/difficult to replicate because it requires:
- Operating a trusted signed crawler infrastructure at scale.
- A production marketplace of high-signal skills that generate real trajectories.
- Volume of closed-loop executions for statistical power and compounding.

The moat compounds: more data → better proprietary signals (e.g. "which sequences drive lift on e-commerce sites") → superior products → more usage. 3-5+ year defensibility through unique ownership of this ground truth.

## Why Now (Market Validation)
- Agentic AI market: ~$10B in 2026, growing >40% CAGR. 40% of enterprise apps to embed task agents (Gartner). Outcome/usage pricing shift creates demand for attribution.
- AI Visibility / AEO exploding: Dozens of audit offerings (mostly agency/consulting). Demand for *verifiable, signed proof* over subjective scores. Web Bot Auth (RFC9421) emerging as the standard for real bot identity (adopted/tested by Cloudflare, Google, Akamai etc.).
- MCP (Model Context Protocol) standardizing tool use for agents. Perfect substrate for a composable skills marketplace.
- Gap: No platform owns the full flywheel of (1) verifiable visibility/certification for agents, (2) trusted high-quality action marketplace, (3) longitudinal attribution + intelligence layer that improves both.

Existing assets in production:
- Live aibotauth.com with real signed crawler proofs and Thai/English support.
- Live obolla.com marketplace with billing, MCP registration, expert skills (many agent-ready focused), showcases with real clients (e.g. successcasting.com 100%, Pinpoint), attribution charters.
- Deep technical integration: default visibility skills call `mcp.aibotauth.scan`, proof badges created on behalf of OBOLLA runs, agent-ready orchestrator + fix packs + verify loops.
- Production architecture respected: CF Worker edge for obolla.com + VPS backend (43.128.75.149) for API/DB + strict deploy scripts + health.

## Data Moat as Priority #1 (Non-negotiable)
Four interlocking datasets we alone can build at scale:

1. **AI Citation & Readiness Data** (AIBotAuth primary)
   - Longitudinal scan results (overall score, grade, category passes/fails, specific signals like llms.txt presence, signed bot responses).
   - Proof events (share_id, embed usage, re-scan deltas).
   - Actual citations where observable.

2. **Agent Transaction Data** (OBOLLA primary)
   - Every marketplace workflow run: which skill, which pack steps (incl. MCP calls), inputs (URLs, tasks), costs split (marketplace/LLM).
   - Composition patterns.

3. **Revenue Attribution Data**
   - Link spend on skill → downstream signals (new proof score improvement, creator earnings, buyer reviews claiming ROI, follow-up scans on same URL).
   - Creator payout attribution + platform take.
   - Proxy outcome metrics (e.g. "after auto-fix run, isitagentready % rose from 62 → 100").

4. **AI Behavioral Data**
   - Which skill sequences succeed/fail for which site profiles/stacks.
   - Language/vertical patterns (Thai SME strength).
   - Failure modes (auth blocks, scan limited, etc.).

**Flywheel**: More certified sites → more credible benchmarks and recommendations → more agents/creators run skills → richer attribution + behavior data → sharper certification signals + better skill ranking → defensibility and pricing power.

## Business Model (Real Early Revenue + Sustainable Growth)
- AIBotAuth: Free tier scans + proof links. Paid: monitoring, bulk certs, Growth Monitor, Thailand SME packs, embed usage.
- OBOLLA: Take-rate on skill runs (marketplace fee), premium skill tiers, creator subs.
- **First concrete Revenue Intelligence product (PM-defined)**: "Agent Impact Signals" inside Creator Dashboard + Intelligence API.
  - Creators see: readiness lift on target URLs from their skills, number of improved certified sites, attribution signals.
  - Site owners / agencies will get linked reports.
  - This is powered exclusively by our closed scan → execute → re-measure loop using signed AIBotAuth crawler.
- Joint moat-powered: Paid dashboards, alerts on lift, benchmark APIs.
- Long-term: Outcome-based slices where attribution is strong; data licensing under strict controls.

## Core Philosophy Alignment
- Ruthless honesty: We start from what is *already live* (signed proofs, working MCP integration, real client showcases, billing). No vaporware.
- Production-grade: Everything respects existing PRODUCTION-RULES (VPS for API/DB, CF edge, deploy scripts, health checks with `backend_reachable: true`).
- Data Moat first in every decision.

## Key Risks & Mitigations (Constructive Challenge Applied)
See CHALLENGE section in this doc and separate review process.

## Success Metrics (12-24 months)
- Volume: # scans, # proofs issued, # skill executions, # unique certified domains.
- Moat strength: Longitudinal coverage per domain (re-scans), attribution linkage rate, predictive power (does pre-skill readiness predict post-run improvement?).
- Revenue: Paying creators, ARR from Intelligence products.
- Defensibility: Unique signed bot adoption, exclusive dataset used in rankings/recommendations, switching costs for creators and certified sites.

## Next: Architecture + Execution
See ARCHITECTURE.md (to be created) for data plane, closed loop flows, platform separation, MCP extensions.

Build only what strengthens the moat or creates clear customer value with real feasibility. Instrument everything that touches a URL or a skill run to feed the datasets.

This is the foundation of a real startup, not a side project.
