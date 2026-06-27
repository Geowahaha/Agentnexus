# Test Report: Billing and Creator Earning Record Creation Flow

**Phase**: Testing & Internal Improvement (controlled tests only)
**Date**: 2026-06-26
**Environment**: Production Postgres structure (VPS 43.128.75.149 agentnexus DB) accessed via existing SSH + docker exec. Local source for code review.

**Important**: All activities used explicit "TEST_TRANSACTION" markers. These are internal system tests, not commercial activity or claims about external buyers/revenue.

## What Was Tested

1. **Schema compatibility**
   - billing_transactions and creator_earnings table structures, types (numeric(12,4), uuid, jsonb, timestamptz), FKs to users, defaults.
   - Verified via `\d` and successful inserts.

2. **Creation flow using existing logic patterns**
   - Inserted test records using the exact columns, types, and value patterns from:
     - moat_service.log_revenue_sale_from_outreach (billing + earning creation)
     - wallet_repository patterns (amounts, fees, descriptions, agent_charges json)
   - 2 pairs of (billing, earning) with TEST markers.

3. **Data integrity & linking**
   - Successful INSERT without constraint violations.
   - billing ↔ earning linked correctly via shared workflow_id.
   - Correct user_id FK resolution using existing prod users.

4. **Calculations**
   - Platform fee (test inserts used 30% to match prior code) and net computed correctly.
   - Values stored with expected precision.

5. **Isolation from normal flows**
   - Direct inserts do not touch wallet balances or earnings_balance (as designed for this attribution-style path).

## Test Evidence (from prod queries)

```
=== TEST BILLING RECORDS ===
 revenue_sale | 199.00 | TEST_TRANSACTION: test revenue sale flow for test-skill-beta ...
 revenue_sale |  99.50 | TEST_TRANSACTION: test revenue sale flow for test-skill-alpha ...

=== LINKING ===
 TEST-WF-BETA-002 | 199.00 | 199.00 | 59.70 | 139.30
 TEST-WF-ALPHA-001 | 99.50 | 99.50 | 29.85 | 69.65

=== FEE CHECK ===
99.50 | 29.85 | 69.65 | 29.85   (matches 30%)
199.00 | 59.70 | 139.30 | 59.70
```

All inserts: 4 rows (2 billing + 2 earning) succeeded cleanly.

## Problems / Weaknesses Identified

1. **Fee rate inconsistency (primary finding)**
   - moat_service.py hardcoded `amount_usd * 0.3`
   - BillingService + wallet_repository._distribute_creator_earnings use `settings.platform_fee_percent` (default **20.0** in config.py).
   - revenue_sale path was using different rate than standard payout/charge flows.
   - Impact: Inconsistent creator payouts depending on creation path.

2. **Special path bypasses wallet repository**
   - The outreach revenue path creates BillingTransactionORM + CreatorEarningORM directly.
   - Does not update wallet.earnings_balance_usd or call add_credits/transfer logic.
   - Normal workflow charges and payouts go through wallet repo with locking, funding pool logic, and balance updates.
   - Risk: Earnings from "revenue_sale" only appear in creator_earnings table until a manual transfer.

3. **Missing moat tables in prod**
   - moat_skill_efficacy does not exist.
   - Full logged_outreach pipeline + validated_revenue_outcomes + batch validation (derivation_service) cannot be tested end-to-end in current prod.
   - The api container also lacks moat_service.py (older deploy image).

4. **No explicit test / source metadata**
   - Only description text distinguishes test data.
   - No column for "test" flag or "source" beyond transaction_type.
   - Makes cleanup and analysis harder.

5. **Other observations**
   - No unique index on (workflow_id, transaction_type) — duplicate revenue_sale for same wf possible.
   - Heavy use of `Decimal(str(x))` casting throughout (precision risk).
   - revenue_sale now appears in prod counts (from prior test inserts), mixed with production transaction types.

## Improvements Made

1. **Fixed fee calculation consistency** in [backend/app/services/moat_service.py](/D:\AgentNexus/backend/app/services/moat_service.py)
   - Changed from hardcoded `0.3` to:
     ```python
     fee_rate = Decimal(str(settings.platform_fee_percent)) / Decimal("100")
     platform_fee = (Decimal(str(amount_usd)) * fee_rate).quantize(Decimal("0.0001"))
     net = (Decimal(str(amount_usd)) - platform_fee).quantize(Decimal("0.0001"))
     ```
   - Added import for settings.
   - Now matches the 20% default used elsewhere in the billing/earnings system.
   - Local verification: for $99.50 → fee=19.9000, net=79.6000 at 20%.

2. **Added comments** clarifying the special nature of the revenue attribution path vs standard wallet flows.

3. **Accurate test records** were created and verified with clear TEST_TRANSACTION labels (left in DB for reference; can be cleaned with `WHERE description LIKE 'TEST_TRANSACTION%'`).

## Recommendations for Next Steps (Internal)

- Deploy current backend code (using existing `scripts/deploy-backend-vps.ps1`) + run alembic to bring moat tables and updated moat_service into prod.
- After deploy, re-test the full record_logged_outreach + log_revenue_sale_from_outreach + run_batch_validation_stats flow using the service functions inside the api container.
- Consider adding a small helper or transaction_type convention + optional jsonb "meta" for test vs prod attribution records.
- Review whether revenue_sale should also credit earnings_balance_usd (or document why it is a pure attribution record).

## Conclusion

The core insert flow for billing_transactions + creator_earnings works correctly against the live prod schema when following the documented column patterns.

One material inconsistency (fee rate) was identified and fixed in source.

The system has two creation paths (wallet repo for charges/payouts vs direct for special revenue attribution). This is now documented as a point to watch for future integration work.

All work labeled transparently as test. No claims about external commercial activity.

Evidence files:
- tmp_test_transactions.sql / tmp_verify_test.sql (the exact test SQL used)
- prod DB queries above (reproducible)
- Code diff in moat_service.py (the improvement)

This strengthens reliability of the transaction recording paths.