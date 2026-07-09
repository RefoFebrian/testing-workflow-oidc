WITH base_products AS (
    SELECT
        pt.id AS product_tmpl_id,
        '__import__.tw_product_template_' ||
            regexp_replace(lower(pt.name), '[^a-z0-9]+', '_', 'g') AS ext_id,
        pt.name,
        pp.default_code,
        pt.description,
        pt.kd_mesin AS kode_mesin,
        wps.name AS product_series,
        CASE WHEN pc3.id IS NOT null THEN COALESCE(pc3.name,'') || ' / ' ELSE '' END || INITCAP(pc2.name) || ' / ' || pc.name AS internal_category,
--        CASE WHEN pc3.id IS NOT null THEN COALESCE(pc3.name,'') || ' / ' ELSE '' END || INITCAP(pc2.name) || ' / ' || INITCAP(pc.name) AS internal_category,
--        COALESCE(pc3.name,'') || ' / ' || pc2.name || ' / ' || pc.name AS internal_category,
--        pc2.name || ' / ' || INITCAP(pc.name) AS internal_category,
        'PricelistServiceCategory|' || sc.name AS service_category
    FROM product_template pt
    LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id
    LEFT JOIN wtc_product_series wps
        ON pt.series_id = wps.id
    LEFT JOIN product_category pc
        ON pt.categ_id = pc.id
    LEFT JOIN product_category pc2
        ON pc.parent_id = pc2.id
    LEFT JOIN product_category pc3
        ON pc2.parent_id = pc3.id
    LEFT JOIN wtc_category_product sc
        ON sc.id = pt.category_product_id
      WHERE pc.name = 'ACCEC'
--    WHERE (pc2.name = 'Service' OR pc3.name = 'Service')
--      WHERE pc.name = 'DIRECT GIFT'
--  WHERE pc.name IN ('NONHGP-ASPIRA','NONHGP-BLAZE','NONHGP-FEDERAL','NONHGP-OTHERS')
      AND pt.active IS TRUE
),
attribute_lines AS (
    SELECT
        ptal.product_tmpl_id,
        ptal.id AS ptal_id,
        pa.name AS attribute_name,
        string_agg(
            pav.code,
            ',' ORDER BY pav.sequence, pav.id
        ) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS attribute_value_codes,
        string_agg(
            regexp_replace(trim(pav.name), '\s+', ' ', 'g'),
            ',' ORDER BY pav.sequence, pav.id
        ) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS attribute_value_names,
        string_agg(
            upper(trim(pav.code)) || '|' || upper(regexp_replace(trim(pav.name), '\s+', ' ', 'g')),
            ' || ' ORDER BY pav.sequence, pav.id
        ) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS attribute_value_mapping_keys,
        min(pav.sequence) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS first_value_sequence
    FROM product_attribute_line ptal
    JOIN product_attribute pa
        ON pa.id = ptal.attribute_id
    LEFT JOIN product_attribute_line_product_attribute_value_rel rel
        ON rel.line_id = ptal.id
    LEFT JOIN product_attribute_value pav
        ON pav.id = rel.val_id
    GROUP BY
        ptal.product_tmpl_id,
        ptal.id,
        pa.name
),
prepared AS (
    SELECT
        bp.*,
        al.attribute_name,
        al.attribute_value_codes,
        al.attribute_value_names,
        al.attribute_value_mapping_keys,
        row_number() OVER (
            PARTITION BY bp.product_tmpl_id
            ORDER BY coalesce(al.first_value_sequence, 999999), al.ptal_id
        ) AS rn
    FROM base_products bp
    LEFT JOIN attribute_lines al
        ON al.product_tmpl_id = bp.product_tmpl_id
)
SELECT
    CASE WHEN rn = 1 THEN ext_id ELSE '' END AS id,
    CASE WHEN rn = 1 THEN name ELSE '' END AS default_code,
    CASE WHEN rn = 1 THEN COALESCE(default_code,name) ELSE '' END AS name,
    CASE WHEN rn = 1 THEN COALESCE(description,name) ELSE '' END AS description,
    CASE WHEN rn = 1 THEN kode_mesin ELSE '' END AS "Kode Mesin",
    CASE WHEN rn = 1 THEN product_series ELSE '' END AS "Product Series",
    CASE WHEN rn = 1 THEN internal_category ELSE '' END AS "Internal Category",
    CASE WHEN rn = 1 THEN service_category ELSE '' END AS "Service Category",
    CASE WHEN rn = 1 THEN 'Umum' ELSE '' END AS division,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS sale_ok,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS purchase_ok,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS is_storable,
    CASE WHEN rn = 1 THEN 'False' ELSE '' END AS lot_valuated,
    CASE WHEN rn = 1 THEN 'none' ELSE '' END AS tracking,
--    CASE WHEN rn = 1 THEN 'Service' ELSE '' END AS type,
    CASE WHEN rn = 1 THEN 'Goods' ELSE '' END AS type
FROM prepared
ORDER BY product_tmpl_id, rn;


-- Product Sparepart
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
AND COALESCE(cat3.name || ' / ' || cat2.name || ' / ' || cat.name, COALESCE(cat2.name || ' / ' || cat.name, cat.name)) ILIKE '%Sparepart%';