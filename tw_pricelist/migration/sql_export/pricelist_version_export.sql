-- Pricelist Version
SELECT
    ppv.name AS name,
    '' AS area,
    ppv.date_start AS start_date,
    ppv.date_end AS end_date,
    pp.name AS price_list,
    'Active' AS state
FROM product_pricelist_version ppv
LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id;