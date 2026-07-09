-- ==============================================================================
-- Migration Script: wtc_pricelist_expedition to product.pricelist
-- Format: Odoo Excel Import (Nested One2many lines using ROW_NUMBER)
-- Source: TEDS 1.0 (wtc_pricelist_expedition, wtc_pricelist_expedition_line, wtc_pricelist_expedition_line_detail)
-- Target: TEDS 2.0 (product.pricelist -> tw.product.pricelist.version -> product.pricelist.item)
-- ==============================================================================

WITH RawData AS (
    SELECT 
        pe.id AS pe_id,
        pe.name AS pricelist_name,
        pe.active AS pricelist_active,
        pe_line.id AS pe_line_id,
        pe_line.name AS version_name,
        pe_line.start_date,
        pe_line.end_date,
        pe_line.active AS version_active,
        detail.id AS detail_id,
        pt.default_code AS product_code,
        detail.cost
    FROM wtc_pricelist_expedition pe
    INNER JOIN wtc_pricelist_expedition_line pe_line 
        ON pe_line.pricelist_expedition_id = pe.id
    INNER JOIN wtc_pricelist_expedition_line_detail detail 
        ON detail.pricelist_expedition_line_id = pe_line.id
    LEFT JOIN product_template pt ON pt.id = detail.product_template_id
),
RankedData AS (
    SELECT 
        *,
        ROW_NUMBER() OVER(
            PARTITION BY pe_id 
            ORDER BY pe_line_id, detail_id
        ) as rn_pricelist,
        ROW_NUMBER() OVER(
            PARTITION BY pe_line_id 
            ORDER BY detail_id
        ) as rn_version
    FROM RawData
)
SELECT 
    -- 1. Header (product.pricelist)
    CASE WHEN rn_pricelist = 1 THEN 'expedition_pricelist_' || pe_id ELSE '' END AS "id",
    CASE WHEN rn_pricelist = 1 THEN pricelist_name ELSE '' END AS "Name",
    CASE WHEN rn_pricelist = 1 THEN 'Purchase' ELSE '' END AS "Pricelist Type",
    CASE WHEN rn_pricelist = 1 THEN CASE WHEN pricelist_active THEN 'TRUE' ELSE 'FALSE' END ELSE '' END AS "Active",
    
    -- 2. Version (One2many: version_ids -> tw.product.pricelist.version)
    CASE WHEN rn_version = 1 THEN 'expedition_version_' || pe_line_id ELSE '' END AS "Version/id",
    CASE WHEN rn_version = 1 THEN COALESCE(version_name, 'Version ' || start_date::VARCHAR) ELSE '' END AS "Version/Name",
    CASE WHEN rn_version = 1 THEN COALESCE(start_date::VARCHAR, '') ELSE '' END AS "Version/Start Date",
    CASE WHEN rn_version = 1 THEN COALESCE(end_date::VARCHAR, '') ELSE '' END AS "Version/End Date",
    
    -- 3. Items (Nested One2many: version_ids/item_ids -> product.pricelist.item)
    'expedition_item_' || detail_id AS "Version/Price List Items/id",
    'Product' AS "Version/Price List Items/Apply On",
    COALESCE(product_code, '') AS "Version/Price List Items/Product/default_code",
    'Fixed Price' AS "Version/Price List Items/Compute Price",
    cost AS "Version/Price List Items/Fixed Price"
FROM RankedData
ORDER BY pe_id, pe_line_id, detail_id;
