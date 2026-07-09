-- =========================================================================
-- SQL Export / Migration Query: wtc.category.product -> tw.selection
-- Target: PricelistServiceCategory in Odoo 18 (tw.selection)
-- Location: tw_work_order/migration/sql_export/category_product_migration.sql
-- =========================================================================

----------------------------------------------------------------------------
-- Odoo-Compatible Export Query (For Excel/CSV Migration Tool)
-- This format generates an export-compatible file with External IDs (XML IDs).
-- The external IDs are standardized to align with the XML definitions 
-- inside tw_pricelist (tw_pricelist_data_service_category_...).
-- Paste this output into an Excel file and import it directly into tw.selection.
----------------------------------------------------------------------------
SELECT 
    'tw_pricelist.tw_pricelist_data_service_category_' || LOWER(REPLACE(TRIM(name), ' ', '')) AS id,
    UPPER(REPLACE(TRIM(name), ' ', '')) AS name,
    'PricelistServiceCategory' AS type,
    LOWER(REPLACE(TRIM(name), ' ', '')) AS value,
    'TRUE' AS active,
    10 AS sequence
FROM 
    wtc_category_product
ORDER BY 
    name;

