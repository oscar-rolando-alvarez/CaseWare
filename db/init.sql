-- =============================================================================
-- init.sql — Schema + Deterministic Seed Data
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Schema
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    country     TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    case_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'closed')),
    updated_at  TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_updated_at ON customers (updated_at);
CREATE INDEX IF NOT EXISTS idx_cases_updated_at     ON cases     (updated_at);
CREATE INDEX IF NOT EXISTS idx_cases_customer_id    ON cases     (customer_id);

-- ---------------------------------------------------------------------------
-- Seed — Customers (30 deterministic rows)
-- ---------------------------------------------------------------------------
INSERT INTO customers (name, email, country, updated_at) VALUES
  ('Alice Martin',       'alice.martin@example.com',       'US',  NOW() - INTERVAL '30 days'),
  ('Bob Chen',           'bob.chen@example.com',           'CA',  NOW() - INTERVAL '29 days'),
  ('Carlos Diaz',        'carlos.diaz@example.com',        'MX',  NOW() - INTERVAL '28 days'),
  ('Diana Patel',        'diana.patel@example.com',        'IN',  NOW() - INTERVAL '27 days'),
  ('Ethan Kowalski',     'ethan.kowalski@example.com',     'PL',  NOW() - INTERVAL '26 days'),
  ('Fiona O''Brien',     'fiona.obrien@example.com',       'IE',  NOW() - INTERVAL '25 days'),
  ('George Kim',         'george.kim@example.com',         'KR',  NOW() - INTERVAL '24 days'),
  ('Hannah Müller',      'hannah.muller@example.com',      'DE',  NOW() - INTERVAL '23 days'),
  ('Ivan Petrov',        'ivan.petrov@example.com',        'RU',  NOW() - INTERVAL '22 days'),
  ('Julia Santos',       'julia.santos@example.com',       'BR',  NOW() - INTERVAL '21 days'),
  ('Kevin Okafor',       'kevin.okafor@example.com',       'NG',  NOW() - INTERVAL '20 days'),
  ('Laura Rossi',        'laura.rossi@example.com',        'IT',  NOW() - INTERVAL '19 days'),
  ('Miguel Torres',      'miguel.torres@example.com',      'ES',  NOW() - INTERVAL '18 days'),
  ('Nadia Dubois',       'nadia.dubois@example.com',       'FR',  NOW() - INTERVAL '17 days'),
  ('Oscar Lindqvist',    'oscar.lindqvist@example.com',    'SE',  NOW() - INTERVAL '16 days'),
  ('Priya Sharma',       'priya.sharma@example.com',       'IN',  NOW() - INTERVAL '15 days'),
  ('Quentin Dupont',     'quentin.dupont@example.com',     'BE',  NOW() - INTERVAL '14 days'),
  ('Rachel Green',       'rachel.green@example.com',       'GB',  NOW() - INTERVAL '13 days'),
  ('Samuel Asante',      'samuel.asante@example.com',      'GH',  NOW() - INTERVAL '12 days'),
  ('Tanya Ivanova',      'tanya.ivanova@example.com',      'UA',  NOW() - INTERVAL '11 days'),
  ('Umar Farouk',        'umar.farouk@example.com',        'PK',  NOW() - INTERVAL '10 days'),
  ('Valentina Cruz',     'valentina.cruz@example.com',     'CO',  NOW() - INTERVAL '9 days'),
  ('William Zhang',      'william.zhang@example.com',      'CN',  NOW() - INTERVAL '8 days'),
  ('Xena Papadopoulos',  'xena.papadopoulos@example.com',  'GR',  NOW() - INTERVAL '7 days'),
  ('Yuki Tanaka',        'yuki.tanaka@example.com',        'JP',  NOW() - INTERVAL '6 days'),
  ('Zara Ahmed',         'zara.ahmed@example.com',         'AE',  NOW() - INTERVAL '5 days'),
  ('Aaron Walsh',        'aaron.walsh@example.com',        'AU',  NOW() - INTERVAL '4 days'),
  ('Beatrice Nyong',     'beatrice.nyong@example.com',     'CM',  NOW() - INTERVAL '3 days'),
  ('Chris Andersen',     'chris.andersen@example.com',     'DK',  NOW() - INTERVAL '2 days'),
  ('Demi Nakamura',      'demi.nakamura@example.com',      'JP',  NOW() - INTERVAL '1 day');

-- ---------------------------------------------------------------------------
-- Seed — Cases (210 deterministic rows, diverse keywords)
-- ---------------------------------------------------------------------------
-- Customer 1 — billing / payments
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (1, 'Billing discrepancy Q1',           'Customer reported incorrect billing amount on Q1 invoice. Possible double-charge on payments gateway.', 'open',        NOW() - INTERVAL '30 days'),
  (1, 'Overdue payment escalation',       'Payment outstanding for 60 days. Escalation required per billing policy SLA.', 'in_progress', NOW() - INTERVAL '29 days'),
  (1, 'Invoice reconciliation failure',   'Automated reconciliation job failed to match billing records with payments ledger.', 'closed',      NOW() - INTERVAL '28 days'),
  (1, 'Duplicate billing charge',         'Duplicate charge detected on customer account. Refund initiated via payments processor.', 'closed',      NOW() - INTERVAL '27 days'),
  (1, 'Billing address update request',   'Customer requested billing address update. Compliance check required before change.', 'open',        NOW() - INTERVAL '26 days'),
  (1, 'Payment gateway timeout',          'Payment gateway returned timeout error during billing cycle. Retry logic triggered.', 'in_progress', NOW() - INTERVAL '25 days'),
  (1, 'Subscription billing failure',     'Monthly subscription billing failed due to expired card. Retry and notification sent.', 'open',        NOW() - INTERVAL '24 days');

-- Customer 2 — audit / compliance
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (2, 'Annual compliance audit initiated','Annual compliance audit started per regulatory schedule. Documents requested from customer.', 'open',        NOW() - INTERVAL '30 days'),
  (2, 'Audit finding: missing KYC docs',  'Audit revealed incomplete KYC documentation. Compliance team flagged for immediate remediation.', 'in_progress', NOW() - INTERVAL '29 days'),
  (2, 'SOC2 compliance gap report',       'Internal audit identified SOC2 control gaps. Remediation plan submitted to compliance officer.', 'in_progress', NOW() - INTERVAL '28 days'),
  (2, 'GDPR data retention audit',        'Compliance audit of data retention policies. Customer data purge schedule requires review.', 'open',        NOW() - INTERVAL '27 days'),
  (2, 'Regulatory reporting compliance',  'Quarterly regulatory report due. Compliance team requires data export from all systems.', 'closed',      NOW() - INTERVAL '26 days'),
  (2, 'Audit trail integrity check',      'Audit log integrity verification requested. SHA-256 checksums compared for compliance.', 'closed',      NOW() - INTERVAL '25 days'),
  (2, 'PCI-DSS compliance review',        'PCI-DSS audit scope expanded. Compliance officer requested additional evidence collection.', 'open',        NOW() - INTERVAL '24 days');

-- Customer 3 — fraud / AML
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (3, 'Suspicious transaction alert',     'AML monitoring flagged suspicious transaction pattern. Fraud investigation opened.', 'open',        NOW() - INTERVAL '30 days'),
  (3, 'AML threshold breach',             'Transaction volume exceeded AML reporting threshold. Suspicious Activity Report filed.', 'in_progress', NOW() - INTERVAL '29 days'),
  (3, 'Fraud attempt: card testing',      'Card testing fraud pattern detected. Multiple small payments followed by large transaction.', 'closed',      NOW() - INTERVAL '28 days'),
  (3, 'Identity fraud investigation',     'Possible identity fraud detected during onboarding. Biometric verification initiated.', 'in_progress', NOW() - INTERVAL '27 days'),
  (3, 'AML name screening hit',           'Customer name matched OFAC sanctions list during AML screening. Case escalated.', 'open',        NOW() - INTERVAL '26 days'),
  (3, 'Fraud ring linkage detected',      'Graph analysis linked customer to known fraud ring. AML and fraud teams collaborating.', 'open',        NOW() - INTERVAL '25 days'),
  (3, 'Money laundering suspicion',       'Unusual layering transactions detected. AML analyst assigned for manual review.', 'in_progress', NOW() - INTERVAL '24 days');

-- Customer 4 — onboarding / reconciliation
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (4, 'Onboarding KYC incomplete',        'Customer onboarding stalled. KYC documents not submitted within required window.', 'open',        NOW() - INTERVAL '30 days'),
  (4, 'Reconciliation: bank statement',   'Bank statement reconciliation failed. 3 transactions unmatched in payments ledger.', 'in_progress', NOW() - INTERVAL '29 days'),
  (4, 'Onboarding risk assessment',       'Enhanced due diligence required for onboarding. Risk score above threshold.', 'open',        NOW() - INTERVAL '28 days'),
  (4, 'Account reconciliation mismatch',  'Monthly account reconciliation detected $500 discrepancy. Audit trail reviewed.', 'closed',      NOW() - INTERVAL '27 days'),
  (4, 'Onboarding document expiry',       'Onboarding documents expired. Customer re-verification required per compliance policy.', 'in_progress', NOW() - INTERVAL '26 days'),
  (4, 'GL reconciliation discrepancy',    'General ledger reconciliation found unposted entries. Finance and billing teams notified.', 'open',        NOW() - INTERVAL '25 days'),
  (4, 'New customer onboarding review',   'Full onboarding review for high-value customer. Compliance and fraud checks pending.', 'in_progress', NOW() - INTERVAL '24 days');

-- Customer 5 — mixed billing + audit
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (5, 'Billing audit Q4 findings',        'Q4 billing audit found overcharges in reconciliation batch. Compliance informed.', 'open',        NOW() - INTERVAL '23 days'),
  (5, 'Payment reconciliation audit',     'External auditor requested payment reconciliation records for last 12 months.', 'in_progress', NOW() - INTERVAL '22 days'),
  (5, 'Billing system migration',         'Billing system migration audit. Reconciliation of historical payments in progress.', 'open',        NOW() - INTERVAL '21 days'),
  (5, 'Compliance billing exception',     'Billing exception flagged by compliance: non-standard payment terms applied.', 'closed',      NOW() - INTERVAL '20 days'),
  (5, 'Invoice dispute resolution',       'Customer disputed invoice citing incorrect payments allocation. Audit scheduled.', 'in_progress', NOW() - INTERVAL '19 days'),
  (5, 'Tax compliance billing review',    'Tax authority requested billing records. Compliance team preparing audit package.', 'open',        NOW() - INTERVAL '18 days'),
  (5, 'Billing fraud suspicion',          'Unusual billing pattern suggesting possible internal fraud. Investigation underway.', 'open',        NOW() - INTERVAL '17 days');

-- Customer 6 — payments + onboarding
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (6, 'Failed onboarding payment',        'Onboarding fee payment failed. Customer unable to complete registration.', 'open',        NOW() - INTERVAL '23 days'),
  (6, 'Payment method onboarding',        'Customer onboarding new payment method. Compliance validation in progress.', 'in_progress', NOW() - INTERVAL '22 days'),
  (6, 'Cross-border payment compliance',  'Cross-border payments require enhanced compliance check. AML screening initiated.', 'open',        NOW() - INTERVAL '21 days'),
  (6, 'Payment reversal dispute',         'Customer disputed payment reversal. Billing and payments team reviewing transaction.', 'closed',      NOW() - INTERVAL '20 days'),
  (6, 'Recurring payment setup failure',  'Recurring payment mandate failed during onboarding. Technical investigation open.', 'in_progress', NOW() - INTERVAL '19 days'),
  (6, 'High-value payment alert',         'Payment exceeding threshold triggered AML alert. Fraud team notified.', 'open',        NOW() - INTERVAL '18 days'),
  (6, 'Payment processor reconciliation', 'Monthly reconciliation of payment processor settlements pending.', 'closed',      NOW() - INTERVAL '17 days');

-- Customer 7 — AML + compliance
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (7, 'AML enhanced due diligence',       'Customer triggered AML enhanced due diligence criteria. Compliance review underway.', 'open',        NOW() - INTERVAL '22 days'),
  (7, 'Compliance policy breach',         'Customer action detected as potential compliance policy breach. Legal notified.', 'in_progress', NOW() - INTERVAL '21 days'),
  (7, 'AML transaction monitoring alert', 'AML monitoring system raised alert on bulk cash transactions. Analyst reviewing.', 'open',        NOW() - INTERVAL '20 days'),
  (7, 'Regulatory compliance deadline',   'Compliance filing deadline approaching. Documentation incomplete. Priority escalation.', 'in_progress', NOW() - INTERVAL '19 days'),
  (7, 'AML risk model update',            'AML risk scoring model updated. Customer re-assessed and escalated.', 'closed',      NOW() - INTERVAL '18 days'),
  (7, 'Compliance training gap',          'Customer representative failed compliance training. Account restricted pending re-training.', 'open',        NOW() - INTERVAL '17 days'),
  (7, 'AML watchlist match review',       'Automated AML watchlist match requires human review. Compliance officer assigned.', 'in_progress', NOW() - INTERVAL '16 days');

-- Customer 8 — fraud + billing
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (8, 'Chargeback fraud investigation',   'Multiple chargebacks indicate possible friendly fraud. Billing and fraud teams engaged.', 'open',        NOW() - INTERVAL '22 days'),
  (8, 'Billing manipulation suspicion',   'Anomalous billing adjustments detected. Possible internal billing fraud. Audit opened.', 'in_progress', NOW() - INTERVAL '21 days'),
  (8, 'Synthetic identity fraud',         'Onboarding data analysis revealed synthetic identity indicators. Fraud case escalated.', 'open',        NOW() - INTERVAL '20 days'),
  (8, 'Fraud loss reconciliation',        'Confirmed fraud losses require reconciliation with insurance. Billing team notified.', 'closed',      NOW() - INTERVAL '19 days'),
  (8, 'Payment fraud pattern',            'Machine learning model flagged payment sequences as fraud pattern. Investigation open.', 'open',        NOW() - INTERVAL '18 days'),
  (8, 'Account takeover attempt',         'Credential stuffing attempt detected. Fraud and compliance teams alerted.', 'in_progress', NOW() - INTERVAL '17 days'),
  (8, 'Refund fraud scheme',              'Customer submitting fraudulent refund requests. Billing audit initiated.', 'open',        NOW() - INTERVAL '16 days');

-- Customer 9 — reconciliation + audit
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (9, 'Intercompany reconciliation',      'Intercompany reconciliation failed for month-end close. Finance team investigating.', 'open',        NOW() - INTERVAL '21 days'),
  (9, 'Audit: reconciliation controls',   'External audit reviewing reconciliation controls. Evidence gathering in progress.', 'in_progress', NOW() - INTERVAL '20 days'),
  (9, 'Bank reconciliation exception',    'Bank reconciliation process found uncleared items exceeding tolerance.', 'open',        NOW() - INTERVAL '19 days'),
  (9, 'Year-end audit preparation',       'Year-end audit preparation. Reconciliation of all sub-ledgers required.', 'closed',      NOW() - INTERVAL '18 days'),
  (9, 'Reconciliation automation failure','Automated reconciliation workflow failed. Manual intervention and audit required.', 'in_progress', NOW() - INTERVAL '17 days'),
  (9, 'Cash reconciliation discrepancy',  'Daily cash reconciliation discrepancy of $1,200. Billing team investigating.', 'open',        NOW() - INTERVAL '16 days'),
  (9, 'Treasury reconciliation audit',    'Treasury team audit of foreign currency reconciliation. Compliance sign-off needed.', 'open',        NOW() - INTERVAL '15 days');

-- Customer 10 — onboarding + compliance
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (10, 'Onboarding compliance checklist', 'Onboarding compliance checklist incomplete. 5 mandatory controls not satisfied.', 'open',        NOW() - INTERVAL '21 days'),
  (10, 'KYC refresh compliance',          'Annual KYC refresh required. Customer compliance documentation needs updating.', 'in_progress', NOW() - INTERVAL '20 days'),
  (10, 'Onboarding AML screening',        'AML screening during onboarding returned adverse media result. Case opened.', 'open',        NOW() - INTERVAL '19 days'),
  (10, 'Compliance breach notification',  'Regulatory body notified of compliance breach during onboarding review.', 'in_progress', NOW() - INTERVAL '18 days'),
  (10, 'Customer onboarding escalation',  'Customer onboarding escalated to senior compliance officer for review.', 'open',        NOW() - INTERVAL '17 days'),
  (10, 'Onboarding data quality issue',   'Poor data quality identified during onboarding. Reconciliation of records required.', 'closed',      NOW() - INTERVAL '16 days'),
  (10, 'New market onboarding check',     'Customer expanding to new market. Compliance and AML onboarding checks required.', 'in_progress', NOW() - INTERVAL '15 days');

-- Customers 11–30 — distributed cases covering all keywords
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (11, 'Billing statement error',         'Customer received incorrect billing statement. Payments applied to wrong account.', 'open',        NOW() - INTERVAL '20 days'),
  (11, 'AML periodic review',             'Scheduled AML periodic review for high-risk customer segment.', 'in_progress', NOW() - INTERVAL '18 days'),
  (11, 'Reconciliation sign-off delay',   'Monthly reconciliation sign-off delayed. Compliance approval pending.', 'open',        NOW() - INTERVAL '15 days'),
  (12, 'Fraud velocity check failure',    'Transaction velocity exceeded fraud thresholds. Payments blocked pending review.', 'open',        NOW() - INTERVAL '20 days'),
  (12, 'Onboarding document review',      'Onboarding documents require compliance review before account activation.', 'in_progress', NOW() - INTERVAL '17 days'),
  (12, 'Billing adjustment audit trail',  'Audit trail for billing adjustments missing entries. Compliance gap identified.', 'closed',      NOW() - INTERVAL '14 days'),
  (13, 'AML suspicious wire transfer',    'Wire transfer pattern matches AML typology. Analyst assigned for review.', 'open',        NOW() - INTERVAL '19 days'),
  (13, 'Payment compliance hold',         'Payment placed on compliance hold pending AML clearance.', 'in_progress', NOW() - INTERVAL '16 days'),
  (13, 'Customer reconciliation request', 'Customer requested full account reconciliation. Billing team processing.', 'open',        NOW() - INTERVAL '13 days'),
  (14, 'Compliance data breach report',   'Potential compliance data breach identified. Audit and legal teams engaged.', 'open',        NOW() - INTERVAL '19 days'),
  (14, 'Billing cycle reconciliation',    'End-of-billing-cycle reconciliation showing variances. Investigation open.', 'in_progress', NOW() - INTERVAL '15 days'),
  (14, 'Fraud chargeback escalation',     'High-value chargeback escalated to fraud team. Payment processor notified.', 'closed',      NOW() - INTERVAL '12 days'),
  (15, 'Onboarding fraud screen',         'Fraud screening during onboarding identified high-risk indicators.', 'open',        NOW() - INTERVAL '18 days'),
  (15, 'AML transaction report filing',   'AML reporting obligation triggered. Suspicious transaction report in preparation.', 'in_progress', NOW() - INTERVAL '14 days'),
  (15, 'Payment reconciliation dispute',  'Payment reconciliation dispute between customer and billing team.', 'open',        NOW() - INTERVAL '11 days'),
  (16, 'Audit committee report',          'Quarterly audit committee report requires reconciliation summary and billing data.', 'closed',      NOW() - INTERVAL '18 days'),
  (16, 'Compliance onboarding review',    'Compliance team reviewing enhanced onboarding procedures for VIP customers.', 'in_progress', NOW() - INTERVAL '13 days'),
  (16, 'Fraud detection model update',    'Fraud detection model retrained on new patterns. Compliance sign-off required.', 'open',        NOW() - INTERVAL '10 days'),
  (17, 'Billing error correction',        'Billing error correction requires reconciliation with payments system.', 'open',        NOW() - INTERVAL '17 days'),
  (17, 'AML beneficial ownership',        'AML investigation into beneficial ownership structure. Compliance filing required.', 'in_progress', NOW() - INTERVAL '12 days'),
  (17, 'Fraud network mapping',           'Fraud network mapping exercise. Compliance and AML teams coordinating.', 'open',        NOW() - INTERVAL '9 days'),
  (18, 'Onboarding delay investigation',  'Onboarding process delay investigation. Compliance bottleneck identified.', 'open',        NOW() - INTERVAL '17 days'),
  (18, 'Reconciliation exception report', 'Reconciliation exception report generated 50 unmatched items. Billing review needed.', 'in_progress', NOW() - INTERVAL '11 days'),
  (18, 'Payment fraud dispute',           'Customer disputing payment as fraud. Investigation and reconciliation in progress.', 'closed',      NOW() - INTERVAL '8 days'),
  (19, 'Compliance gap remediation',      'Compliance gap remediation plan approved. Billing and payments controls updated.', 'open',        NOW() - INTERVAL '16 days'),
  (19, 'AML case escalation',             'AML case escalated to financial intelligence unit. Case documentation prepared.', 'in_progress', NOW() - INTERVAL '10 days'),
  (19, 'Billing policy review',           'Billing policy review triggered by compliance audit findings.', 'open',        NOW() - INTERVAL '7 days'),
  (20, 'Fraud risk assessment',           'Customer fraud risk assessment updated. Enhanced monitoring applied.', 'in_progress', NOW() - INTERVAL '16 days'),
  (20, 'Onboarding AML complete',         'Onboarding AML checks completed. Customer cleared for account activation.', 'closed',      NOW() - INTERVAL '9 days'),
  (20, 'Reconciliation batch failure',    'Overnight reconciliation batch failed. Payments team investigating root cause.', 'open',        NOW() - INTERVAL '6 days'),
  (21, 'Billing compliance exception',    'Billing compliance exception raised by internal audit. Root cause analysis open.', 'open',        NOW() - INTERVAL '15 days'),
  (21, 'Fraud AML crossover case',        'Case involves both fraud indicators and AML red flags. Joint investigation opened.', 'in_progress', NOW() - INTERVAL '8 days'),
  (21, 'Payments reconciliation audit',   'Payments reconciliation audit requested by external compliance body.', 'open',        NOW() - INTERVAL '5 days'),
  (22, 'Onboarding compliance passed',    'Onboarding compliance checks passed. Customer fully onboarded.', 'closed',      NOW() - INTERVAL '15 days'),
  (22, 'AML monitoring upgrade',          'AML monitoring system upgrade. Historical transactions re-screened for compliance.', 'in_progress', NOW() - INTERVAL '7 days'),
  (22, 'Billing fraud ring',              'Billing records linked to known fraud ring. AML and billing teams alerted.', 'open',        NOW() - INTERVAL '4 days'),
  (23, 'Reconciliation tool migration',   'Reconciliation tool migration audit. Payments data validated post-migration.', 'open',        NOW() - INTERVAL '14 days'),
  (23, 'Compliance training completion',  'Compliance training completed by customer team. Onboarding resumed.', 'closed',      NOW() - INTERVAL '6 days'),
  (23, 'Fraud pattern analysis',          'Advanced fraud pattern analysis using transaction graph. AML overlap identified.', 'in_progress', NOW() - INTERVAL '3 days'),
  (24, 'AML country risk change',         'Customer country risk rating changed. AML re-assessment and compliance review required.', 'open',        NOW() - INTERVAL '14 days'),
  (24, 'Billing overpayment refund',      'Customer overpaid invoice. Reconciliation and refund via payments processor.', 'closed',      NOW() - INTERVAL '5 days'),
  (24, 'Onboarding regulatory hold',      'Customer onboarding on regulatory hold. Compliance and legal review in progress.', 'in_progress', NOW() - INTERVAL '2 days'),
  (25, 'Fraud recovery plan',             'Post-fraud recovery plan initiated. Billing adjustments and compliance report filed.', 'open',        NOW() - INTERVAL '13 days'),
  (25, 'AML annual review',               'Annual AML review for Tier-1 customer. Enhanced due diligence documentation required.', 'in_progress', NOW() - INTERVAL '4 days'),
  (25, 'Reconciliation audit sign-off',   'Reconciliation audit completed. Sign-off from compliance officer received.', 'closed',      NOW() - INTERVAL '1 day'),
  (26, 'Compliance status update',        'Regulatory compliance status update required by board. Billing and audit data needed.', 'open',        NOW() - INTERVAL '12 days'),
  (26, 'Onboarding background check',     'Enhanced background check during onboarding. Fraud and AML results pending.', 'in_progress', NOW() - INTERVAL '3 days'),
  (26, 'Payment dispute billing',         'Payment dispute escalated to billing arbitration. Compliance oversight applied.', 'open',        NOW() - INTERVAL '1 day'),
  (27, 'AML de-risking review',           'AML de-risking review initiated. Customer relationship under assessment.', 'open',        NOW() - INTERVAL '12 days'),
  (27, 'Billing system audit',            'Full billing system audit. Reconciliation of 12 months of transactions required.', 'in_progress', NOW() - INTERVAL '2 days'),
  (27, 'Fraud prevention update',         'Fraud prevention controls updated post-incident. Compliance sign-off obtained.', 'closed',      NOW() - INTERVAL '1 day'),
  (28, 'Onboarding PEP check',            'Politically Exposed Person (PEP) check during onboarding. AML protocol activated.', 'open',        NOW() - INTERVAL '11 days'),
  (28, 'Reconciliation data quality',     'Data quality issues affecting reconciliation accuracy. Billing records being corrected.', 'in_progress', NOW() - INTERVAL '1 day'),
  (28, 'Compliance fine assessment',      'Regulatory compliance fine assessment. Billing impact analysis underway.', 'open',        NOW() - INTERVAL '1 day'),
  (29, 'Fraud claim investigation',       'Customer fraud claim investigation. Payments and billing records subpoenaed.', 'in_progress', NOW() - INTERVAL '10 days'),
  (29, 'AML filing deadline',             'AML suspicious activity report filing deadline today. Compliance officer notified.', 'open',        NOW() - INTERVAL '1 day'),
  (29, 'Reconciliation sign-off audit',   'Quarterly reconciliation sign-off audit. All billing entries validated.', 'closed',      NOW() - INTERVAL '1 day'),
  (30, 'Onboarding final review',         'Final onboarding review for corporate customer. Compliance and fraud checks complete.', 'closed',      NOW() - INTERVAL '9 days'),
  (30, 'AML transaction deep dive',       'Deep-dive AML transaction analysis. Reconciliation of payment flows required.', 'in_progress', NOW() - INTERVAL '1 day'),
  (30, 'Billing compliance close-out',    'Billing compliance close-out report. All reconciliation items resolved.', 'open',        NOW() - INTERVAL '1 day');

-- ---------------------------------------------------------------------------
-- Additional cases for customers 11–30 (4 per customer = 80 rows)
-- Brings total seed cases from 130 → 210 (≥ 200 required)
-- ---------------------------------------------------------------------------
INSERT INTO cases (customer_id, title, description, status, updated_at) VALUES
  (11, 'Fraud transaction reversal',      'Customer requested reversal of flagged fraud transaction. Payments team reviewing billing records.', 'open',        NOW() - INTERVAL '16 days'),
  (11, 'Onboarding KYC escalation',       'KYC escalation during onboarding. AML team requested additional identity verification documents.', 'in_progress', NOW() - INTERVAL '13 days'),
  (11, 'Compliance audit follow-up',      'Follow-up items from last compliance audit. Billing and reconciliation controls reviewed.', 'closed',      NOW() - INTERVAL '10 days'),
  (11, 'Payment gateway reconciliation',  'Payment gateway reconciliation discrepancy flagged. Billing team investigating missing settlements.', 'open',        NOW() - INTERVAL '7 days'),
  (12, 'AML risk re-assessment',          'Customer AML risk re-assessment triggered by unusual payment pattern. Compliance review initiated.', 'open',        NOW() - INTERVAL '16 days'),
  (12, 'Billing dispute escalation',      'Customer escalated billing dispute. Payments reconciliation required to validate charges.', 'in_progress', NOW() - INTERVAL '12 days'),
  (12, 'Compliance onboarding gap',       'Compliance gap identified during onboarding phase. Remediation plan submitted.', 'open',        NOW() - INTERVAL '9 days'),
  (12, 'Fraud alert investigation',       'Automated fraud alert triggered. Transaction analysis and AML screening in progress.', 'closed',      NOW() - INTERVAL '6 days'),
  (13, 'Billing credit note issuance',    'Credit note issued for overbilled payments. Reconciliation entry posted to general ledger.', 'closed',      NOW() - INTERVAL '15 days'),
  (13, 'Onboarding sanctions screening',  'Onboarding sanctions screening returned a potential match. AML compliance review required.', 'open',        NOW() - INTERVAL '11 days'),
  (13, 'Fraud recovery billing',          'Billing adjustments required following confirmed fraud case. Reconciliation with insurer ongoing.', 'in_progress', NOW() - INTERVAL '8 days'),
  (13, 'Audit evidence collection',       'External audit evidence collection phase. Billing records and reconciliation data requested.', 'open',        NOW() - INTERVAL '5 days'),
  (14, 'AML enhanced monitoring',         'Customer placed under AML enhanced monitoring. Transaction reports filed with compliance officer.', 'in_progress', NOW() - INTERVAL '16 days'),
  (14, 'Onboarding payment failure',      'Initial onboarding payment failed. Billing team notified; retry process initiated.', 'open',        NOW() - INTERVAL '11 days'),
  (14, 'Reconciliation period close',     'Month-end reconciliation period close. All billing entries validated and signed off.', 'closed',      NOW() - INTERVAL '8 days'),
  (14, 'Fraud suspicious login',          'Suspicious login activity detected. Fraud and compliance teams notified; account under review.', 'open',        NOW() - INTERVAL '4 days'),
  (15, 'Billing proration error',         'Proration error in billing cycle. Payments incorrectly calculated; reconciliation underway.', 'open',        NOW() - INTERVAL '15 days'),
  (15, 'Compliance policy update',        'Compliance policy update requires re-acknowledgement. Onboarding workflow updated accordingly.', 'in_progress', NOW() - INTERVAL '10 days'),
  (15, 'AML SAR submission',              'Suspicious Activity Report submitted to regulatory authority. AML case documentation complete.', 'closed',      NOW() - INTERVAL '7 days'),
  (15, 'Reconciliation variance audit',   'Reconciliation variance audit initiated. Billing and payments ledgers cross-checked.', 'open',        NOW() - INTERVAL '3 days'),
  (16, 'Onboarding AML adverse media',    'Adverse media hit during onboarding AML screening. Enhanced due diligence required.', 'open',        NOW() - INTERVAL '15 days'),
  (16, 'Billing refund processing',       'Billing refund processing delayed. Payments processor confirmation awaited; compliance notified.', 'in_progress', NOW() - INTERVAL '9 days'),
  (16, 'Fraud claim closed',              'Customer fraud claim resolved. Reconciliation of reimbursed payments completed.', 'closed',      NOW() - INTERVAL '6 days'),
  (16, 'Compliance internal review',      'Internal compliance review of onboarding procedures. Audit findings to be addressed.', 'open',        NOW() - INTERVAL '2 days'),
  (17, 'AML periodic transaction review', 'Periodic AML transaction review for medium-risk customer. No new flags identified.', 'closed',      NOW() - INTERVAL '14 days'),
  (17, 'Billing invoice correction',      'Invoice correction issued after reconciliation identified overpayment. Payments adjusted.', 'open',        NOW() - INTERVAL '10 days'),
  (17, 'Onboarding risk upgrade',         'Customer risk rating upgraded during onboarding review. Additional compliance checks required.', 'in_progress', NOW() - INTERVAL '6 days'),
  (17, 'Fraud pattern flagged',           'New fraud pattern flagged by monitoring system. AML and billing teams assessing exposure.', 'open',        NOW() - INTERVAL '3 days'),
  (18, 'Compliance audit preparation',    'Compliance audit preparation in progress. Billing records and reconciliation evidence being compiled.', 'open',        NOW() - INTERVAL '14 days'),
  (18, 'AML transaction alert closed',    'AML transaction alert reviewed and closed. No suspicious activity confirmed after investigation.', 'closed',      NOW() - INTERVAL '9 days'),
  (18, 'Billing overage dispute',         'Customer disputing billing overage. Payments team reconciling usage records.', 'in_progress', NOW() - INTERVAL '5 days'),
  (18, 'Onboarding compliance sign-off',  'Onboarding compliance sign-off received. Customer account activated pending billing setup.', 'open',        NOW() - INTERVAL '2 days'),
  (19, 'Fraud chargeback reversal',       'Chargeback reversal initiated for confirmed fraud transaction. Billing team processing refund.', 'closed',      NOW() - INTERVAL '13 days'),
  (19, 'AML watchlist re-screen',         'Periodic AML watchlist re-screening completed. Customer cleared; compliance record updated.', 'closed',      NOW() - INTERVAL '8 days'),
  (19, 'Reconciliation tool error',       'Reconciliation tool error caused incorrect billing entries. Finance team correcting records.', 'open',        NOW() - INTERVAL '4 days'),
  (19, 'Onboarding document expired',     'Onboarding document expired during process. Compliance team requesting updated KYC records.', 'in_progress', NOW() - INTERVAL '1 day'),
  (20, 'Compliance reporting deadline',   'Compliance reporting deadline imminent. Billing and reconciliation data extraction in progress.', 'in_progress', NOW() - INTERVAL '13 days'),
  (20, 'AML beneficial owner update',     'AML beneficial ownership disclosure updated. Compliance verification and audit trail created.', 'open',        NOW() - INTERVAL '7 days'),
  (20, 'Billing tax adjustment',          'Tax adjustment applied to billing account. Reconciliation of prior payments required.', 'closed',      NOW() - INTERVAL '4 days'),
  (20, 'Fraud early warning alert',       'Early warning fraud alert based on peer comparison. Investigation opened; AML notified.', 'open',        NOW() - INTERVAL '2 days'),
  (21, 'Onboarding identity mismatch',    'Identity mismatch detected during onboarding. Fraud and compliance teams reviewing documents.', 'open',        NOW() - INTERVAL '12 days'),
  (21, 'AML transaction log review',      'Full AML transaction log review requested by compliance. Payments data exported for analysis.', 'in_progress', NOW() - INTERVAL '7 days'),
  (21, 'Billing correction approved',     'Billing correction approved by finance. Reconciliation entry posted; customer notified.', 'closed',      NOW() - INTERVAL '4 days'),
  (21, 'Reconciliation SLA breach',       'Reconciliation SLA breached. Compliance escalation raised; billing team on remediation.', 'open',        NOW() - INTERVAL '1 day'),
  (22, 'Fraud velocity anomaly',          'Fraud velocity anomaly detected in payments stream. AML screening triggered automatically.', 'open',        NOW() - INTERVAL '12 days'),
  (22, 'Compliance sign-off pending',     'Compliance sign-off pending for updated billing terms. Onboarding process on hold.', 'in_progress', NOW() - INTERVAL '6 days'),
  (22, 'Reconciliation discrepancy note', 'Reconciliation discrepancy note issued. Finance and billing teams resolving open items.', 'open',        NOW() - INTERVAL '3 days'),
  (22, 'AML case review complete',        'AML case review completed. No reportable activity; compliance file closed.', 'closed',      NOW() - INTERVAL '1 day'),
  (23, 'Billing late payment notice',     'Late payment notice issued. Compliance team reviewing billing terms and payment history.', 'open',        NOW() - INTERVAL '11 days'),
  (23, 'Onboarding risk reassessment',    'Risk reassessment during onboarding flagged potential AML concerns. Investigation pending.', 'in_progress', NOW() - INTERVAL '7 days'),
  (23, 'Fraud document forgery',          'Suspected document forgery during onboarding. Fraud and compliance teams investigating.', 'open',        NOW() - INTERVAL '4 days'),
  (23, 'Reconciliation close confirmation','Reconciliation close confirmation received from external auditor. Billing records certified.', 'closed',      NOW() - INTERVAL '1 day'),
  (24, 'Compliance training required',    'Compliance training required for customer account team. Onboarding restricted until complete.', 'open',        NOW() - INTERVAL '11 days'),
  (24, 'AML dual-control review',         'AML dual-control review process initiated for high-value transactions. Compliance sign-off needed.', 'in_progress', NOW() - INTERVAL '6 days'),
  (24, 'Billing reconciliation locked',   'Billing reconciliation locked pending external audit. Finance team coordinating with compliance.', 'open',        NOW() - INTERVAL '3 days'),
  (24, 'Fraud account freeze lifted',     'Fraud investigation complete. Account freeze lifted; billing and payments resumed normally.', 'closed',      NOW() - INTERVAL '1 day'),
  (25, 'Onboarding final compliance',     'Final compliance review for onboarding completed. Customer cleared for all payment services.', 'closed',      NOW() - INTERVAL '10 days'),
  (25, 'Billing dispute mediation',       'Billing dispute referred to mediation. Reconciliation data submitted as evidence.', 'open',        NOW() - INTERVAL '6 days'),
  (25, 'AML re-screening result',         'AML re-screening result negative. Compliance record updated; no further action required.', 'closed',      NOW() - INTERVAL '3 days'),
  (25, 'Fraud ring cross-reference',      'Customer accounts cross-referenced with known fraud ring. AML and billing audit underway.', 'in_progress', NOW() - INTERVAL '1 day'),
  (26, 'Reconciliation audit complete',   'Annual reconciliation audit complete. Billing variances resolved; compliance approval obtained.', 'closed',      NOW() - INTERVAL '10 days'),
  (26, 'AML source of funds review',      'AML source of funds review initiated. Compliance officer reviewing payment history.', 'open',        NOW() - INTERVAL '5 days'),
  (26, 'Billing system reconciliation',   'Billing system reconciliation post-upgrade. Payments data integrity verified by audit team.', 'in_progress', NOW() - INTERVAL '3 days'),
  (26, 'Fraud loss assessment',           'Fraud loss assessment completed. Billing adjustments and insurance claim filed by compliance.', 'open',        NOW() - INTERVAL '1 day'),
  (27, 'Onboarding AML cleared',          'AML clearance received for new customer onboarding. Compliance file archived; billing activated.', 'closed',      NOW() - INTERVAL '9 days'),
  (27, 'Compliance exception handling',   'Compliance exception handling process triggered. Billing and payments flagged for manual review.', 'open',        NOW() - INTERVAL '5 days'),
  (27, 'Fraud suspicious withdrawal',     'Suspicious withdrawal detected. AML monitoring alert raised; fraud team investigating.', 'in_progress', NOW() - INTERVAL '3 days'),
  (27, 'Reconciliation variance closed',  'Reconciliation variance closed after audit. Billing correction posted to ledger.', 'closed',      NOW() - INTERVAL '1 day'),
  (28, 'AML transaction freeze',          'AML transaction freeze applied to account. Compliance hold pending investigation outcome.', 'in_progress', NOW() - INTERVAL '9 days'),
  (28, 'Billing audit response',          'Response to billing audit findings submitted. Reconciliation supporting documents attached.', 'open',        NOW() - INTERVAL '5 days'),
  (28, 'Onboarding enhanced review',      'Enhanced onboarding review for high-net-worth customer. AML and fraud checks extended.', 'open',        NOW() - INTERVAL '3 days'),
  (28, 'Fraud detection escalation',      'Fraud detection score exceeded threshold. Case escalated to senior analyst for compliance review.', 'closed',      NOW() - INTERVAL '1 day'),
  (29, 'Compliance corrective action',    'Corrective action plan submitted following compliance finding. Billing controls updated.', 'open',        NOW() - INTERVAL '8 days'),
  (29, 'AML model recalibration',         'AML risk model recalibrated for customer segment. Compliance approved new scoring thresholds.', 'closed',      NOW() - INTERVAL '4 days'),
  (29, 'Billing payment plan setup',      'Payment plan set up for overdue billing balance. Reconciliation scheduled on plan completion.', 'in_progress', NOW() - INTERVAL '2 days'),
  (29, 'Fraud impact reconciliation',     'Fraud impact reconciliation finalised. Billing restatement submitted to compliance officer.', 'open',        NOW() - INTERVAL '1 day'),
  (30, 'Compliance re-certification',     'Annual compliance re-certification completed. Billing and AML records archived for audit trail.', 'closed',      NOW() - INTERVAL '8 days'),
  (30, 'Onboarding payments validation',  'Payments validation step in onboarding completed. Billing account created; reconciliation seeded.', 'open',        NOW() - INTERVAL '4 days'),
  (30, 'AML suspicious pattern closed',   'AML suspicious pattern investigation closed. No reportable activity; compliance file updated.', 'closed',      NOW() - INTERVAL '2 days'),
  (30, 'Fraud billing discrepancy',       'Fraud-related billing discrepancy identified. Reconciliation and compliance report in progress.', 'in_progress', NOW() - INTERVAL '1 day');
