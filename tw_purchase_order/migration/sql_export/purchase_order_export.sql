-- Purchase Order
SELECT
    CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Vendor" END AS "Vendor"
    , CASE WHEN rn = 1 THEN "Vendor Reference" END AS "Vendor Reference"
    -- , CASE WHEN rn = 1 THEN "PO Type" END AS "PO Type"
    , CASE WHEN rn = 1 THEN "PO Type / Database ID" END AS "PO Type / Database ID"
    , CASE WHEN rn = 1 THEN "Payment Terms" END AS "Payment Terms"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Order Deadline" END AS "Order Deadline"
    , CASE WHEN rn = 1 THEN "Expected Arrival"  END AS "Expected Arrival" 
    -- , CASE WHEN rn = 1 THEN "Deliver To" END AS "Deliver To"
    , CASE WHEN rn = 1 THEN "Deliver To / Database ID" END AS "Deliver To / Database ID"
    , "Order Lines / External ID"
    -- , "Order Lines / Product"
    , "Order Lines / Product / Database ID"
    , "Order Lines / Quantity"
    , "Order Lines / Received Qty"
    , "Order Lines / Manual Received Qty"
    , "Order Lines / Consolidated Qty"
    , "Order Lines / Unit of Measure"
    , "Order Lines / Unit Price"
    , "Order Lines / Taxes"
FROM (
    SELECT 
        '__import__.purchase.order_' || po.id AS "External ID"
		, wb.code AS "Branch"
		, rp.default_code AS "Vendor"
		, po.partner_ref AS "Vendor Reference"
        -- , wpot.name AS "PO Type"
		, wpot.name AS "PO Type / Database ID"
		, apt.name AS "Payment Terms"
		, TO_CHAR(po.start_date, 'YYYY-MM-DD') AS "Start Date"
		, TO_CHAR(po.end_date, 'YYYY-MM-DD') AS "End Date"
		, po.division AS "Division"
		, (po.date_order + interval '7 hours') AS "Order Deadline"
		, (po.date_order + interval '7 hours') AS "Expected Arrival" 
        -- , 'WH ' || deliver.name || ': Receipts' AS "Deliver To"
		, 'WH ' || deliver.name || ': Receipts' AS "Deliver To / Database ID"
		, '__import__.purchase.order.line_' || pol.id AS "Order Lines / External ID"
        -- , '[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')' AS "Order Lines / Product"
		, '[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')' AS "Order Lines / Product / Database ID"
		, pol.product_qty AS "Order Lines / Quantity"
		, pol.received AS "Order Lines / Received Qty"
		, pol.qty_invoiced AS "Order Lines / Manual Received Qty"
		, CASE WHEN pol.qty_invoiced > 0 THEN pol.qty_invoiced ELSE NULL END AS "Order Lines / Consolidated Qty"
		, REGEXP_REPLACE(pu.name, '\(s\)', 's') AS "Order Lines / Unit of Measure"
		, pol.price_unit AS "Order Lines / Unit Price"
		, REGEXP_REPLACE(tax.name, '[()]', '', 'g') AS "Order Lines / Taxes"
		, ROW_NUMBER() OVER (PARTITION BY po.name ORDER BY pol.id) AS rn
    FROM purchase_order po 
	LEFT JOIN wtc_branch wb ON po.branch_id = wb.id
	LEFT JOIN (
		SELECT 
		    sp.transaction_id
			, JSON_AGG(sp.id) picking_ids
		FROM stock_picking sp
		JOIN ir_model im ON sp.model_id = im.id AND im.model = 'purchase.order'
		WHERE 1=1
		AND sp.state NOT IN ('draft', 'cancel', 'done')
		GROUP BY sp.transaction_id
	) picking ON picking.transaction_id = po.id
	LEFT JOIN (
		SELECT
			ai.transaction_id
			, JSON_AGG(ai.id) invoice_ids
		FROM account_invoice ai
		JOIN ir_model im ON ai.model_id = im.id AND im.model = 'purchase.order'
		WHERE 1=1
		AND ai.type = 'in_invoice'
		AND ai.state NOT IN ('cancel', 'paid')
		GROUP BY ai.transaction_id
	) invoice ON invoice.transaction_id = po.id
	LEFT JOIN res_partner rp ON po.partner_id = rp.id
	LEFT JOIN wtc_purchase_order_type wpot ON po.purchase_order_type_id = wpot.id
	LEFT JOIN account_payment_term apt ON po.payment_term_id = apt.id
	LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
	LEFT JOIN wtc_branch deliver ON spt.branch_id = deliver.id
	LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
	LEFT JOIN product_product pp ON pol.product_id = pp.id
	LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
	LEFT JOIN product_attribute_value_product_product_rel pavpp ON pavpp.prod_id = pp.id
	LEFT JOIN product_attribute_value pav ON pavpp.att_id = pav.id
	LEFT JOIN product_uom pu ON pol.product_uom = pu.id
	LEFT JOIN purchase_order_taxe pot ON pot.ord_id = pol.id
	LEFT JOIN account_tax tax ON pot.tax_id = tax.id
	WHERE 1=1
	AND po.state = 'approved'
	AND po.division = 'Unit'
	AND (picking.picking_ids IS NOT NULL OR invoice.invoice_ids IS NOT NULL)
) t;

--1 (Get PO Type)
SELECT
	tpot.id
FROM tw_purchase_order_type tpot
WHERE 1=1
AND tpot.division = 'Unit' -- fill from "Division" PO Query TEDS
AND tpot.name = 'Additional'; -- fill from "PO Type / Database ID" PO Query TEDS

--2 (Get Deliver To)
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
AND (spt.division = 'Unit' OR spt.division IS NULL) -- fill from "Division" PO Query TEDS
AND rc.code = 'DDA' -- fill from "Branch" PO Query TEDS
AND sw.name || ': ' || (spt.name ->> 'en_US') ILIKE '%WH Cabang Caman: Receipts%'; -- fill from "Deliver To / Database ID" PO Query TEDS

--3 (Get Product)
SELECT
	prod.id
FROM product_product prod
LEFT JOIN product_template prod_tmpl ON prod_tmpl.id = prod.product_tmpl_id
LEFT JOIN product_variant_combination variant ON prod.id = variant.product_product_id
LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
LEFT JOIN product_category prod_categ ON prod_tmpl.categ_id = prod_categ.id
WHERE 1=1
AND prod_tmpl.division = 'Unit' -- fill from "Division" PO Query TEDS
AND '[' || prod_tmpl.default_code || '] ' || COALESCE(prod_tmpl.name ->> 'en_US', prod_tmpl.description ->> 'en_US') || ' (' || (attr_value.name ->> 'en_US') || ')' ILIKE '%[MRB] SCOOPY FASHION (BLACK)%'; -- fill from "Order Lines / Product / Database ID" PO Query TEDS