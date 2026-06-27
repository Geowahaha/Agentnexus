-- Controlled TEST inserts for testing the billing + earning creation flow
-- All records are explicitly marked TEST_TRANSACTION for transparency
-- Using exact same columns and types as prod schema and moat_service / wallet_repository logic

INSERT INTO billing_transactions (id, user_id, workflow_id, transaction_type, amount_usd, marketplace_cost_usd, llm_cost_usd, balance_after_usd, description, agent_charges, created_at) 
VALUES ('1179c7a3-58a5-4ed9-acab-602f3e5a7239', '6dedd3f7-3a80-47f0-9f89-c003321eab72', 'TEST-WF-ALPHA-001', 'revenue_sale', 99.50, 0, 0, 0, 'TEST_TRANSACTION: test revenue sale flow for test-skill-alpha using existing prod tables', '[{"skill": "test-skill-alpha", "amount": 99.50}]', now());

INSERT INTO creator_earnings (id, creator_id, buyer_id, agent_id, product_type, workflow_id, gross_amount_usd, platform_fee_usd, net_amount_usd, created_at) 
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '0b0b771c-afed-47ac-a303-669bdce58062', '6dedd3f7-3a80-47f0-9f89-c003321eab72', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'revenue_report', 'TEST-WF-ALPHA-001', 99.50, 29.85, 69.65, now());

INSERT INTO billing_transactions (id, user_id, workflow_id, transaction_type, amount_usd, marketplace_cost_usd, llm_cost_usd, balance_after_usd, description, agent_charges, created_at) 
VALUES ('3f0a5b18-b323-4423-ab53-4538e2f936fd', '0b0b771c-afed-47ac-a303-669bdce58062', 'TEST-WF-BETA-002', 'revenue_sale', 199.00, 0, 0, 0, 'TEST_TRANSACTION: test revenue sale flow for test-skill-beta using existing prod tables', '[{"skill": "test-skill-beta", "amount": 199.00}]', now());

INSERT INTO creator_earnings (id, creator_id, buyer_id, agent_id, product_type, workflow_id, gross_amount_usd, platform_fee_usd, net_amount_usd, created_at) 
VALUES ('c3d4e5f6-a7b8-9012-cdef-123456789012', '6dedd3f7-3a80-47f0-9f89-c003321eab72', '0b0b771c-afed-47ac-a303-669bdce58062', 'd4e5f6a7-b8c9-0123-def1-234567890123', 'revenue_report', 'TEST-WF-BETA-002', 199.00, 59.70, 139.30, now());
