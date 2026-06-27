-- Verification queries for TEST_TRANSACTION flow test
\echo '=== TEST BILLING RECORDS ==='
SELECT transaction_type, amount_usd, left(description, 70) as desc, workflow_id, created_at 
FROM billing_transactions 
WHERE description LIKE 'TEST_TRANSACTION%' 
ORDER BY created_at DESC;

\echo '=== LINKING: billing <-> earning via workflow_id ==='
SELECT 
  b.workflow_id, 
  b.amount_usd as billing_amt, 
  e.gross_amount_usd as earning_gross, 
  e.platform_fee_usd as fee, 
  e.net_amount_usd as net
FROM billing_transactions b
JOIN creator_earnings e ON e.workflow_id = b.workflow_id
WHERE b.description LIKE 'TEST_TRANSACTION%'
ORDER BY b.created_at DESC;

\echo '=== FEE VERIFICATION (should be 30%) ==='
SELECT 
  gross_amount_usd,
  platform_fee_usd,
  net_amount_usd,
  round(gross_amount_usd * 0.3, 4) as expected_30pct_fee
FROM creator_earnings 
WHERE workflow_id LIKE 'TEST-WF-%';
