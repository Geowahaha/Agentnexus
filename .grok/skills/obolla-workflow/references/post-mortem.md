# Post-mortem (9arm — adapted for OBOLLA)

Draft only after **all four** are true:

- [ ] Reliable repro
- [ ] Root cause known (mechanism, not guess)
- [ ] Fix identified (commit/PR)
- [ ] Fix validated (repro passes, health OK if production)

## Structure

1. **Summary** (mandatory) — what broke, what fixed, owner
2. Symptom — concrete error/log/API field
3. **Root cause** (mandatory) — code paths, files, commits
4. Why symptom followed from cause
5. **Fix** (mandatory) — why it addresses root cause, not symptom
6. How it was found — repro, tools, rejected hypotheses (from breadcrumb ledger)
7. Why it slipped through — CI gap, latent code, review miss (blameless)
8. **Validation** (mandatory) — health, verify %, test names; state coverage honestly
9. Action items — owner + artifact, or "None"

Refuse to draft if fix not validated. For customer-facing summary, shorten mechanism — keep engineering record complete.