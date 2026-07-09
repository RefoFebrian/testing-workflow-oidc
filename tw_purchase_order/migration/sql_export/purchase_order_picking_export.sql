-- Purchase Order Picking
SELECT
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
	, CASE WHEN rn = 1 THEN "Partner" END AS "Partner"
	, CASE WHEN rn = 1 THEN "Division" END AS "Division"
	, CASE WHEN rn = 1 THEN "Operation Type / Database ID" END AS "Operation Type / Database ID"
	, CASE WHEN rn = 1 THEN "Destination Location" END AS "Destination Location"
	, CASE WHEN rn = 1 THEN "Scheduled Date" END AS "Scheduled Date"
	, CASE WHEN rn = 1 THEN "Source Document" END AS "Source Document" -- fill from "name" fields trx after PO Import
	, "Stock move / External ID"
	, "Stock move / Branch"
	, "Stock move / Description"
	, "Stock move / Product / Database ID"
	, "Stock move / Initial Qty"
	, "Stock move / Quantity"
	, "Stock move / Demand"
	, "Stock move / Created Purchase Order Lines / External ID"
FROM (
	SELECT
	    '__import__.stock.picking_' || sp.id AS "External ID"
	    , rp.default_code AS "Partner"
	    , sp.division AS "Division"
	    , 'WH ' || deliver.name || ': Receipts' AS "Operation Type / Database ID"
	    , 'WH-' || wb.code || '/' || sl.name AS "Destination Location"
		, (sp.min_date + INTERVAL '7 hours') AS "Scheduled Date"
	    , sp.origin AS "Source Document"
	    , '__import__.stock.move_' || sm.id AS "Stock move / External ID"
	    , wb.code AS "Stock move / Branch"
	    , COALESCE(
	        '[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')',
	        '[' || pt.name || '] ' || pt.description
	    ) AS "Stock move / Description"
	    , COALESCE(
	        '[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')',
	        '[' || pt.name || '] ' || pt.description
	    ) AS "Stock move / Product / Database ID"
	    , sm.product_uom_qty AS "Stock move / Initial Qty"
	    , sm.product_uom_qty AS "Stock move / Quantity"
	    , sm.product_uom_qty AS "Stock move / Demand"
	    , '__import__.purchase.order.line_' || sm.purchase_line_id AS "Stock move / Created Purchase Order Lines / External ID"
	    , ROW_NUMBER() OVER (PARTITION BY sp.origin ORDER BY sm.id) AS rn
	FROM stock_picking sp
	LEFT JOIN wtc_branch wb ON sp.branch_id = wb.id
	LEFT JOIN res_partner rp ON sp.partner_id = rp.id
	LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
	LEFT JOIN wtc_branch deliver ON spt.branch_id = deliver.id
	LEFT JOIN stock_move sm ON sm.picking_id = sp.id
	LEFT JOIN product_product pp ON sm.product_id = pp.id
	LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
	LEFT JOIN product_attribute_value_product_product_rel pavpp ON pavpp.prod_id = pp.id
	LEFT JOIN product_attribute_value pav ON pavpp.att_id = pav.id
	LEFT JOIN stock_location sl ON sm.location_dest_id = sl.id
	WHERE 1=1
	AND sp.division IN ('Unit', 'Sparepart')
	AND sp.origin ILIKE 'PO/%'
	AND sm.id IS NOT NULL
	AND sp.state NOT IN ('cancel', 'done')
) t;

--1 (Get Operation Type)
SELECT
	spt.id
FROM stock_picking_type spt
LEFT JOIN res_company rc ON spt.company_id = rc.id
LEFT JOIN stock_location source_loc ON spt.default_location_src_id = source_loc.id
LEFT JOIN stock_location dest_loc ON spt.default_location_dest_id = dest_loc.id
LEFT JOIN stock_warehouse sw ON spt.warehouse_id = sw.id
WHERE 1=1
AND spt.code = 'incoming'
AND spt.use_create_lots IS TRUE
AND (spt.division = 'Unit' OR spt.division IS NULL) -- fill from "Division" PO Picking Query TEDS
AND rc.code = 'DDA' -- fill from "Branch" PO Query TEDS
AND sw.name || ': ' || (spt.name ->> 'en_US') ILIKE '%WH Cabang Caman: Receipts%'; -- fill from "Operation Type / Database ID" PO Picking Query TEDS

--2 (Get Product)
SELECT
	prod.id
FROM product_product prod
LEFT JOIN product_template prod_tmpl ON prod_tmpl.id = prod.product_tmpl_id
LEFT JOIN product_variant_combination variant ON prod.id = variant.product_product_id
LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
LEFT JOIN product_category prod_categ ON prod_tmpl.categ_id = prod_categ.id
WHERE 1=1
AND prod_tmpl.division = 'Unit' -- fill from "Division" PO Picking Query TEDS
AND '[' || prod_tmpl.default_code || '] ' || COALESCE(prod_tmpl.name ->> 'en_US', prod_tmpl.description ->> 'en_US') || ' (' || (attr_value.name ->> 'en_US') || ')' ILIKE '%[MRB] SCOOPY FASHION (BLACK)%'; -- fill from "Stock move / Product / Database ID" PO Picking Query TEDS