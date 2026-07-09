-- Pricelist Item
SELECT
    CASE
        WHEN ppi.categ_id IS NOT NULL THEN 'Category'
        ELSE 'Product'
    END AS display_applied_on,
    COALESCE(pc3.name || ' / ', '') ||
    COALESCE(pc2.name || ' / ', '') ||
    COALESCE(pc.name, '') AS category,
    CASE
        WHEN ppi.categ_id IS NOT NULL THEN ''
        ELSE ppi.name
    END AS product,
    CASE
        WHEN pp_v.id IS NOT NULL THEN
            COALESCE(pt_direct.name, '')
        ELSE ''
    END AS variant,
    CASE
        WHEN ppi.base = -1 THEN 'Formula'
        WHEN ppi.base = 1 THEN 'Fixed Price'
        ELSE ''
    END AS compute_price,
    ppi.min_quantity AS min_quantity,
    ppv.name AS pricelist_version,
    pp.name AS pricelist,
    ppv.date_start AS start_date,
    ppv.date_end AS end_date,
    CASE
        WHEN ppi.base = 1 THEN 'Sales Price'
        WHEN ppi.base = -1 THEN 'Other Pricelist'
        ELSE ''
    END AS based_on,
    COALESCE(other_pp.name, '') AS other_pricelist,
    ppi.price_discount AS price_discount,
    ppi.price_round AS price_rounding,
    ppi.price_max_margin AS max_price_margin,
    ppi.price_min_margin AS min_price_margin,
    ppi.price_surcharge AS extra_fee,
    ppi.price_surcharge AS fixed_price
FROM product_pricelist pp
LEFT JOIN product_pricelist_version ppv ON ppv.pricelist_id = pp.id
LEFT JOIN product_pricelist_item ppi ON ppi.price_version_id = ppv.id
LEFT JOIN product_category pc ON pc.id = ppi.categ_id
LEFT JOIN product_category pc2 ON pc2.id = pc.parent_id
LEFT JOIN product_category pc3 ON pc3.id = pc2.parent_id
LEFT JOIN product_product pp_v ON pp_v.id = ppi.product_id
LEFT JOIN product_template pt ON pt.id = pp_v.product_tmpl_id
LEFT JOIN product_pricelist other_pp ON other_pp.id = ppi.base_pricelist_id
LEFT JOIN product_template pt_direct ON pt_direct.id = ppi.product_tmpl_id
WHERE ppi.base IN (1, -1)
ORDER BY pp.name, ppv.name;