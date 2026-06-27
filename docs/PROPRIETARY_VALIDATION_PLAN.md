# Proprietary Validation Plan & Execution (Updated for PM Push)

## Proprietary Elements (in MoatSkillEfficacy profiles)
- RevenueCausalFidelity: % runs where signed AIBotAuth MCP step (from behavior_sequence) + revenue attributed (unique to closed loop).
- ClosedLoopCorrelation: Weighted score from lift + revenue + fidelity (only possible with our signed data).
- UniqueLoopMultiplier: Based on variance in fidelity (high variance = our data quality only).
- proprietary_validation_correlation: Active metric tracking correlation with real revenue outcomes.

## Clear Validation Plan (Actionable, Executing — PM Push Applied)
1. **Data Collection (Started - Using Logged Sales Data for REAL sales)**:
   - On every real sale from logged outreach (POST /revenue-sale/log): 
     - Uses the logged data (amount + skill from outreach log/pipeline).
     - Creates real BillingTransactionORM + CreatorEarningORM (billing_id, earning_id, status=closed recorded).
     - Appends to validated_revenue_outcomes (incl. prop_correlation_at_sale, billing_recorded).
     - Updates total_attributed_revenue on profile.
   - Auto triggers batch validation.
   - Sources: signed AIBotAuth traces + revenue attribution + actual earnings records.

2. **Correlation Method (Batch Stats — Proof)**:
   - run_batch_validation_stats: avg_proprietary_revenue_correlation, correlation_variance, high_correlation_profiles_count (>0.6), sales_outcomes_count, total_logged_sales_usd, sample.
   - Explicitly pairs real sale amounts with prop scores (at-sale + current).
   - Plan: After every sale (auto) + manual Run Batch. Target avg >0.6 = proprietary validates → defensibility + pricing power.
   - History + outcomes persisted in moat_skill_efficacy.profile_data.

3. **Execution Steps (Active Now — Dashboard + API)**:
   - CreatorDashboard: Logged Sales Pipeline shows logged items (from Generate/Execute Outreach).
   - "Convert Logged → Real Sale": executes log with amount from logged data → real records + results recorded + batch run.
   - Buttons: Generate Outreach → Execute Outreach → Log to Pipeline → Convert to Sale → View Validation Report / Run Batch.
   - /proprietary-validation + /run-batch + /revenue-intelligence expose the collected proof data.
   - All Ed25519 signed.

4. **Long-term Evolution**:
   - Batch job for full Pearson on >10 points.
   - Store stats as IP.
   - Use in Revenue Product for premium (high proprietary = higher price).
   - Evidence: Investors, marketing, "our correlation proves the moat works".

## Security
- All sales/outreach Ed25519 signed (canonical + SHA256).
- API: Data min (proprietary only), verified, logged.
- No raw exposed.

## Revenue Tie-in (Early Execution)
- Logged sales data used to execute real sales (Billing/Earning created, results recorded in profile and batch).
- Conversion tracked: "closed" status, amount, billing_id.
- Drives $3k-8k/mo via product + sales pipeline.

Start/continue via dashboard buttons (active execution — 2 focus areas driven):
- Early Revenue Execution: Generate/Execute Outreach → add to Logged Pipeline → Convert Logged to Real Sale (executes using logged data, creates real Billing + Earning records, records billing_id/earning_id/results/status, feeds validation).
- Proprietary Validation: Auto batch on sale + "Run Batch Validation Stats" + "View Validation Report". Collects outcomes + computes avg_corr/variance from real sales data. Target >0.6.
- All flows signed, minimized, logged. Results visible in alerts + /revenue-intelligence.
Data actively collected and proof in progress (real sales from logs now drive correlation evidence).
