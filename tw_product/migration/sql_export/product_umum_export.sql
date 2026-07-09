-- Product Umum
SELECT
	'__import__.product.template_' || pt.id AS "External ID"
	, COALESCE(pt.description, pt.name) AS "Name"
	, pt.name AS "Default Code"
	, COALESCE(cat3.name || ' / ' || cat2.name || ' / ' || cat.name, COALESCE(cat2.name || ' / ' || cat.name, cat.name)) AS "Product Category"
	, wps.name AS "Product Series"
	, pt.sale_ok AS "Sales"
	, pt.purchase_ok AS "Purchase"
	, CASE
		WHEN pt.type = 'product' THEN 'Goods'
		WHEN pt.type = 'service' THEN 'Service'
		WHEN pt.type = 'consu' THEN 'Goods'
	END AS "Product Type"
	, 'Ordered quantities' AS "Invoicing Policy"
	, TRUE AS "Track Inventory"
	, CASE
		WHEN cat3.name = 'Unit' THEN 'By Unique Serial Number'
		ELSE 'By Quantity'
	END AS "Tracking"
	, CASE
		WHEN cat3.name = 'Unit' THEN TRUE
		ELSE NULL
	END AS "Valuation by Lot/Serial number"
	, CASE
		WHEN pt.list_price < 1 THEN 1
		ELSE pt.list_price
	END AS "Sales Price"
	, 'Units' AS "Unit of Measure"
	, COALESCE(REGEXP_REPLACE(cust_tax.tax, '[()]', '', 'g'), 'PPN OUT 12%') AS "Sales Taxes"
	, COALESCE(REGEXP_REPLACE(supp_tax.tax, '[()]', '', 'g'), 'PPN IN 12%') AS "Purchase Taxes"
	, pt.kd_mesin AS "Kode Mesin"
	, tup.name AS "Unit Parts"
	, wcp.name AS "Service Category"
	, COALESCE(cat3.name, cat2.name) AS "Division"
	, 'Units' AS "Purchase Unit"
	, 'On received quantities' AS "Control Policy"
	, 'Buy' AS "Routes"
	-- , ROW_NUMBER() OVER (PARTITION BY pt.name ORDER BY pt.id) AS rn
FROM product_template pt
LEFT JOIN product_category cat ON pt.categ_id = cat.id
LEFT JOIN product_category cat2 ON cat.parent_id = cat2.id
LEFT JOIN product_category cat3 ON cat2.parent_id = cat3.id
LEFT JOIN wtc_product_series wps ON pt.series_id = wps.id
LEFT JOIN teds_unit_parts tup ON pt.part_unit_id = tup.id
LEFT JOIN (
	SELECT
		DISTINCT pt2.id
		, tax.name tax
	FROM product_taxes_rel ptr
	LEFT JOIN account_tax tax ON ptr.tax_id = tax.id
	LEFT JOIN product_product pp2 ON ptr.prod_id = pp2.id
	LEFT JOIN product_template pt2 ON pp2.product_tmpl_id = pt2.id
	WHERE 1=1
	AND tax.active IS TRUE
	LIMIT 1
) cust_tax ON cust_tax.id = pt.id
LEFT JOIN (
	SELECT
		DISTINCT pt3.id
		, tax.name tax
	FROM product_supplier_taxes_rel pstr
	LEFT JOIN account_tax tax ON pstr.tax_id = tax.id
	LEFT JOIN product_product pp3 ON pstr.prod_id = pp3.id
	LEFT JOIN product_template pt3 ON pp3.product_tmpl_id = pt3.id
	WHERE 1=1
	AND tax.active IS TRUE
	LIMIT 1
) supp_tax ON supp_tax.id = pt.id
LEFT JOIN wtc_category_product wcp ON pt.category_product_id = wcp.id
WHERE 1=1
AND pt.active = TRUE
AND COALESCE(cat3.name || ' / ' || cat2.name || ' / ' || cat.name, COALESCE(cat2.name || ' / ' || cat.name, cat.name)) ILIKE '%Umum%';