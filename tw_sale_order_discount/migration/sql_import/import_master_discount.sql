--Master Discount
SELECT 
	'tw_sale_discount_items_' || (lower(parent_pc.name) || '_' || lower(pc.name)) || '_' || tmd.id AS "External ID",
	parent_pc.name || ' / ' || pc.name AS "Category",
	coalesce(pt.name, pp.default_code) AS "Product",
	tmd.additional AS "Additional",
	tmd.fix AS "Fix",
	tmd.topup AS "Topup",
	tmd.simpart AS "Simpart",
	tmd.hotline AS "Hotline"
FROM teds_master_discount tmd 
LEFT JOIN product_category pc ON pc.id = tmd.categ_id
INNER JOIN product_category parent_pc ON parent_pc.id = pc.parent_id
LEFT JOIN product_product pp ON pp.id = tmd.product_id
LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id