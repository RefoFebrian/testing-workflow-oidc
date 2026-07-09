--Master AHASS TOP
SELECT 
	'tw_master_ahass_top_' || lower(rp.default_code) || '_' || tmat.id AS "External ID",
	CASE 
        WHEN rp.default_code ~ '^[0-9]+$' THEN rp.name
        ELSE rp.default_code
    END AS "Dealer",
	parent_pc.name || ' / ' || pc.name AS "Master AHASS TOP Line / Category",
	wpot.name || '|' || apt.name AS "Master AHASS TOP Line / Discount Cash"
FROM teds_master_ahass_top tmat
LEFT JOIN teds_master_ahass_top_line tmatl ON tmatl.master_ahass_top_id = tmat.id 
LEFT JOIN res_partner rp ON rp.id = tmat.partner_id 
LEFT JOIN product_category pc ON pc.id = tmatl.categ_id
INNER JOIN product_category parent_pc ON parent_pc.id = pc.parent_id
LEFT JOIN teds_master_discount_cash tmdc ON tmdc.id = tmatl.discount_cash_id 
LEFT JOIN wtc_purchase_order_type wpot ON wpot.id = tmdc.type_id
LEFT JOIN account_payment_term apt ON apt.id = tmdc.payment_term_id 
WHERE 1=1
AND rp.active IS TRUE 
ORDER BY rp.default_code ASC