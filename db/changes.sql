-- =============================================================================
-- changes.sql — Incremental data changes for testing /ingest delta detection
-- Run AFTER init.sql to simulate real-world updates
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Update 5 existing cases (status change + bump updated_at to now)
-- ---------------------------------------------------------------------------
UPDATE cases SET status = 'closed',      updated_at = NOW() WHERE case_id = 1;
UPDATE cases SET status = 'closed',      updated_at = NOW() WHERE case_id = 8;
UPDATE cases SET status = 'in_progress', updated_at = NOW() WHERE case_id = 15;
UPDATE cases SET status = 'open',        updated_at = NOW() WHERE case_id = 22;
UPDATE cases SET status = 'closed',      updated_at = NOW() WHERE case_id = 33;

-- ---------------------------------------------------------------------------
-- Insert 2 new customers
-- ---------------------------------------------------------------------------
INSERT INTO customers (name, email, country, updated_at) VALUES
  ('Elena Vasquez',  'elena.vasquez@example.com',  'AR', NOW()),
  ('Felix Brunner',  'felix.brunner@example.com',  'CH', NOW());

-- ---------------------------------------------------------------------------
-- Insert 10 new cases (referencing the 2 new customers and existing ones)
-- ---------------------------------------------------------------------------
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (31, 'AML onboarding initial review',      'New customer Elena Vasquez requires AML and compliance onboarding checks.', 'open',        NOW()),
  (31, 'Billing setup for new account',      'Initial billing configuration for new customer. Payments method validation required.', 'in_progress', NOW()),
  (32, 'KYC document collection',            'Felix Brunner onboarding: KYC documentation collection initiated per compliance requirements.', 'open',        NOW()),
  (32, 'Compliance risk rating assignment',  'New customer risk rating assignment. AML risk model applied during onboarding.', 'in_progress', NOW()),
  (1,  'Billing reconciliation Q2',          'Q2 billing reconciliation initiated. Cross-check of all payments and invoices required.', 'open',        NOW()),
  (5,  'Fraud indicator follow-up',          'Follow-up on previously identified fraud indicators. AML liaison requested.', 'in_progress', NOW()),
  (10, 'Compliance re-certification',        'Annual compliance re-certification required. Audit documentation package prepared.', 'open',        NOW()),
  (15, 'Payment processing audit',           'Full audit of payment processing pipeline. Reconciliation and billing records reviewed.', 'in_progress', NOW()),
  (20, 'AML re-screening trigger',           'Customer transaction triggered AML re-screening. Compliance hold applied.', 'open',        NOW()),
  (25, 'Reconciliation variance resolution', 'Outstanding reconciliation variance from prior billing period. Finance team resolving.', 'in_progress', NOW());
