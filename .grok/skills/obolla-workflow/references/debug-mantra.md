# Debug Mantra (9arm — adapted for OBOLLA)

Recite **verbatim** as the first thing in the first debug response:

> **Mantra:**
> 1. **First is reproducibility.** Can the issue be reproduced reliably?
> 2. **Know the fail path.** Debugger first; then source trace + knob enumeration; then in-code instrumentation.
> 3. **Question your hypothesis.** What would disprove it?
> 4. **Every run is a breadcrumb.** Cross-reference all of them.

Then apply in order. Do not propose a fix before step 1 is satisfied.

## OBOLLA-specific repro shortcuts

- **API/UI bug:** `curl` or `Invoke-RestMethod` against `https://obolla.com/api/...`
- **Edge/Worker:** check `cloudflare/worker/src/index.ts` route + live response headers
- **Backend:** VPS logs or local `backend/` with same endpoint path
- **Agent-Ready 0% UI:** compare `analyze` vs `verify` responses — different code paths
- **Deploy auth 10000:** scoped `CLOUDFLARE_API_TOKEN` — use `scripts/deploy-obolla.ps1`

## Breadcrumb ledger format

```markdown
| # | Change | Result | Rules in / out |
|---|--------|--------|----------------|
| 1 | ... | pass/fail | hypothesis H1 |
```

Update after every experiment. New hypothesis must fit **all** prior rows.