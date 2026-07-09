-- IDEMPOTENT SQL MIGRATION SEED SCRIPT FOR HOLDING CLAIM CONFIGURATIONS
-- Target Tables: tw_work_order_claim (headers), tw_work_order_claim_line (lines), ir_model_data (external IDs)
-- Handled Claim Types: LCR and KPB (periods: 1, 2, 3, 4)
-- Journal Assigned: 'Journal WO Claim'
-- Configured for: Top-level parent company only (parent_id IS NULL)
-- Default Payment Term: 30 days / 30 Hari

-- 1. Resolve configuration metadata once
WITH config_data AS (
    SELECT
        (SELECT id FROM tw_selection WHERE type = 'WorkOrderClaimType' AND value = 'LCR' LIMIT 1) AS lcr_type_id,
        (SELECT id FROM tw_selection WHERE type = 'WorkOrderClaimType' AND value = 'KPB' LIMIT 1) AS kpb_type_id,
        COALESCE(
            (SELECT default_supplier_id FROM res_company WHERE branch_type_id = (SELECT id FROM tw_selection WHERE type = 'BranchType' AND value = 'MD' LIMIT 1) AND default_supplier_id IS NOT NULL LIMIT 1),
            (SELECT partner_id FROM res_company WHERE branch_type_id = (SELECT id FROM tw_selection WHERE type = 'BranchType' AND value = 'MD' LIMIT 1) LIMIT 1),
            (SELECT id FROM res_partner WHERE name = 'Astra Honda Motor' LIMIT 1),
            7
        ) AS atpm_partner_id,
        COALESCE(
            (SELECT id FROM account_payment_term WHERE COALESCE(name->>'en_US', name->>'id_ID', name::text) ILIKE '%30%' LIMIT 1),
            (SELECT id FROM account_payment_term LIMIT 1)
        ) AS payment_term_id,
        COALESCE((SELECT id FROM res_users WHERE login = 'admin' LIMIT 1), 1) AS user_id
),
-- 2. Resolve KPB product IDs by joining product_product (p) and product_template (t)
kpb_products AS (
    SELECT
        '1' AS period,
        (SELECT p.id FROM product_product p JOIN product_template t ON p.product_tmpl_id = t.id WHERE p.default_code = 'KPB 1' OR t.name->>'en_US' = 'KPB 1' OR t.name->>'id_ID' = 'KPB 1' LIMIT 1) AS product_id
    UNION ALL
    SELECT
        '2' AS period,
        (SELECT p.id FROM product_product p JOIN product_template t ON p.product_tmpl_id = t.id WHERE p.default_code = 'KPB 2' OR t.name->>'en_US' = 'KPB 2' OR t.name->>'id_ID' = 'KPB 2' LIMIT 1) AS product_id
    UNION ALL
    SELECT
        '3' AS period,
        (SELECT p.id FROM product_product p JOIN product_template t ON p.product_tmpl_id = t.id WHERE p.default_code = 'KPB 3' OR t.name->>'en_US' = 'KPB 3' OR t.name->>'id_ID' = 'KPB 3' LIMIT 1) AS product_id
    UNION ALL
    SELECT
        '4' AS period,
        (SELECT p.id FROM product_product p JOIN product_template t ON p.product_tmpl_id = t.id WHERE p.default_code = 'KPB 4' OR t.name->>'en_US' = 'KPB 4' OR t.name->>'id_ID' = 'KPB 4' LIMIT 1) AS product_id
),
-- 3. Resolve LCR product IDs by joining product_product (p) and product_template (t) matching all input product name variations (ILIKE)
lcr_products AS (
    SELECT 
        COALESCE(t.name->>'id_ID', t.name->>'en_US', 'Claim LCR') AS descr,
        p.id AS product_id
    FROM product_product p 
    JOIN product_template t ON p.product_tmpl_id = t.id 
    WHERE t.name->>'en_US' ILIKE '%Claim Layanan Cek Rangka (LCR)%' 
       OR t.name->>'id_ID' ILIKE '%Claim Layanan Cek Rangka (LCR)%' 
       OR p.default_code ILIKE '%Claim Layanan Cek Rangka (LCR)%'
       OR t.name->>'en_US' ILIKE '%Claim Check & Treatment%' 
       OR t.name->>'id_ID' ILIKE '%Claim Check & Treatment%' 
       OR p.default_code ILIKE '%Claim Check & Treatment%'
       OR t.name->>'en_US' ILIKE '%Claim Perbaikan Rangka%' 
       OR t.name->>'id_ID' ILIKE '%Claim Perbaikan Rangka%' 
       OR p.default_code ILIKE '%Claim Perbaikan Rangka%'
),
-- 4. Get Top-Level Parent Companies (parent_id IS NULL)
h2z_company AS (
    SELECT id, name, code FROM res_company WHERE parent_id IS NULL
),
-- 5. Prepare master claim configurations to be inserted
claim_masters_to_insert AS (
    SELECT
        c.id AS company_id,
        cfg.lcr_type_id AS claim_type_id,
        'LCR' AS type_code,
        NULL::varchar AS kpb_period,
        'LCR - ' || c.name AS display_name,
        COALESCE(
            (SELECT id FROM account_journal WHERE company_id = c.id AND (COALESCE(name->>'en_US', name->>'id_ID', name::text) = 'Journal WO Claim') LIMIT 1),
            (SELECT id FROM account_journal WHERE COALESCE(name->>'en_US', name->>'id_ID', name::text) = 'Journal WO Claim' LIMIT 1)
        ) AS journal_id,
        cfg.payment_term_id,
        cfg.user_id,
        cfg.atpm_partner_id
    FROM h2z_company c
    CROSS JOIN config_data cfg

    UNION ALL

    SELECT
        c.id AS company_id,
        cfg.kpb_type_id AS claim_type_id,
        'KPB' AS type_code,
        p.period AS kpb_period,
        'KPB Ke-' || p.period || ' - ' || c.name AS display_name,
        COALESCE(
            (SELECT id FROM account_journal WHERE company_id = c.id AND (COALESCE(name->>'en_US', name->>'id_ID', name::text) = 'Journal WO Claim') LIMIT 1),
            (SELECT id FROM account_journal WHERE COALESCE(name->>'en_US', name->>'id_ID', name::text) = 'Journal WO Claim' LIMIT 1)
        ) AS journal_id,
        cfg.payment_term_id,
        cfg.user_id,
        cfg.atpm_partner_id
    FROM h2z_company c
    CROSS JOIN (SELECT '1' AS period UNION ALL SELECT '2' UNION ALL SELECT '3' UNION ALL SELECT '4') p
    CROSS JOIN config_data cfg
),
-- 6. Insert new master claims and return their IDs
inserted_masters AS (
    INSERT INTO tw_work_order_claim (
        active, scope_type, company_id, claim_type_id, journal_id, payment_term_id, kpb_period, unit_apply_on, display_name,
        create_uid, write_uid, create_date, write_date
    )
    SELECT
        true, 'branch', company_id, claim_type_id, journal_id, payment_term_id, kpb_period, 'all', display_name,
        user_id, user_id, NOW(), NOW()
    FROM claim_masters_to_insert m
    WHERE NOT EXISTS (
        SELECT 1 FROM tw_work_order_claim existing
        WHERE existing.company_id = m.company_id
          AND existing.claim_type_id = m.claim_type_id
          AND (existing.kpb_period = m.kpb_period OR (existing.kpb_period IS NULL AND m.kpb_period IS NULL))
    )
    RETURNING id, company_id, claim_type_id, kpb_period
),
-- 7. Insert external XML IDs for the newly created master records into ir_model_data
inserted_xml_ids AS (
    INSERT INTO ir_model_data (
        name, module, model, res_id, noupdate
    )
    SELECT
        CASE 
            WHEN m.kpb_period IS NULL THEN 'claim_master_lcr_' || LOWER(COALESCE(c.code, REPLACE(LOWER(c.name), ' ', '_')))
            ELSE 'claim_master_kpb_' || m.kpb_period || '_' || LOWER(COALESCE(c.code, REPLACE(LOWER(c.name), ' ', '_')))
        END AS name,
        'tw_work_order_claim' AS module,
        'tw.work.order.claim' AS model,
        m.id AS res_id,
        true AS noupdate
    FROM inserted_masters m
    JOIN res_company c ON m.company_id = c.id
    WHERE NOT EXISTS (
        SELECT 1 FROM ir_model_data existing
        WHERE existing.module = 'tw_work_order_claim'
          AND existing.name = CASE 
                                  WHEN m.kpb_period IS NULL THEN 'claim_master_lcr_' || LOWER(COALESCE(c.code, REPLACE(LOWER(c.name), ' ', '_')))
                                  ELSE 'claim_master_kpb_' || m.kpb_period || '_' || LOWER(COALESCE(c.code, REPLACE(LOWER(c.name), ' ', '_')))
                              END
    )
    RETURNING id
),
-- 8. Combine newly inserted master claims and existing ones to generate/link line items
all_masters AS (
    SELECT id, company_id, claim_type_id, kpb_period, 'INSERTED' AS src
    FROM inserted_masters
    -- Reference inserted_xml_ids to force PostgreSQL to execute the XML ID insertion CTE
    LEFT JOIN (SELECT COUNT(*) FROM inserted_xml_ids) dummy ON 1=1
    UNION ALL
    SELECT m.id, m.company_id, m.claim_type_id, m.kpb_period, 'EXISTING' AS src
    FROM tw_work_order_claim m
    JOIN config_data cfg ON (m.claim_type_id = cfg.lcr_type_id OR m.claim_type_id = cfg.kpb_type_id)
)
-- 9. Finally insert claim lines dynamically
INSERT INTO tw_work_order_claim_line (
    claim_id, claim_to, claim_description, product_id, partner_id,
    create_uid, write_uid, create_date, write_date
)
-- 9a. Lines for KPB
SELECT
    m.id AS claim_id,
    'atpm' AS claim_to,
    'Claim KPB ' || m.kpb_period AS claim_description,
    p.product_id,
    cfg.atpm_partner_id AS partner_id,
    cfg.user_id AS create_uid,
    cfg.user_id AS write_uid,
    NOW() AS create_date,
    NOW() AS write_date
FROM all_masters m
CROSS JOIN config_data cfg
JOIN kpb_products p ON m.kpb_period = p.period
WHERE m.claim_type_id = cfg.kpb_type_id
  AND p.product_id IS NOT NULL -- Safety check to filter out non-matching products
  -- Only insert if the line with this product doesn't exist for this claim configuration
  AND NOT EXISTS (
      SELECT 1 FROM tw_work_order_claim_line existing_line
      WHERE existing_line.claim_id = m.id
        AND existing_line.product_id = p.product_id
  )

UNION ALL

-- 9b. Lines for LCR
SELECT
    m.id AS claim_id,
    'atpm' AS claim_to,
    l.descr AS claim_description,
    l.product_id,
    cfg.atpm_partner_id AS partner_id,
    cfg.user_id AS create_uid,
    cfg.user_id AS write_uid,
    NOW() AS create_date,
    NOW() AS write_date
FROM all_masters m
CROSS JOIN config_data cfg
CROSS JOIN lcr_products l
WHERE m.claim_type_id = cfg.lcr_type_id
  AND l.product_id IS NOT NULL -- Safety check to filter out non-matching products
  -- Only insert if the line with this product doesn't exist for this claim configuration
  AND NOT EXISTS (
      SELECT 1 FROM tw_work_order_claim_line existing_line
      WHERE existing_line.claim_id = m.id
        AND existing_line.product_id = l.product_id
  );
