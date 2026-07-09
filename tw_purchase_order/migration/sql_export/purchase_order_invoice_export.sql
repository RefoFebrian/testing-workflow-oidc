-- Purchase Order Invoice
SELECT
    CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Company" END AS "Company"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Partner" END AS "Partner"
    , CASE WHEN rn = 1 THEN "Reference" END AS "Reference" -- fill from "name" fields trx after PO Import
    , CASE WHEN rn = 1 THEN "Supplier Invoice Number" END AS "Supplier Invoice Number"
    , CASE WHEN rn = 1 THEN "Invoice/Bill Date" END AS "Invoice/Bill Date"
    , CASE WHEN rn = 1 THEN "Date" END AS "Date"
    , CASE WHEN rn = 1 THEN "Period / Database ID" END AS "Period / Database ID"
    , CASE WHEN rn = 1 THEN "Payment Reference" END AS "Payment Reference" -- fill from "name" fields trx after PO Import
    , CASE WHEN rn = 1 THEN "Recipient Bank" END AS "Recipient Bank"
    , CASE WHEN rn = 1 THEN "Due Date" END AS "Due Date"
    , CASE WHEN rn = 1 THEN "Payment Terms" END AS "Payment Terms"
    , CASE WHEN rn = 1 THEN "Journal" END AS "Journal"
    , CASE WHEN rn = 1 THEN "Combined Tax?" END AS "Combined Tax?"
    -- , CASE WHEN rn = 1 THEN "Discount Lines / Discount Cash" END AS "Discount Lines / Discount Cash"
    -- , CASE WHEN rn = 1 THEN "Discount Lines / Discount Program" END AS "Discount Lines / Discount Program"
    -- , CASE WHEN rn = 1 THEN "Discount Lines / Discount Other" END AS "Discount Lines / Discount Other"
    , "Invoice Lines / External ID"
    , "Invoice Lines / Company"
    , "Invoice Lines / Division"
    , "Invoice Lines / Product / Database ID"
    , "Invoice lines / Purchase Order Line / External ID" -- fill from "Order Lines / External ID" PO Query TEDS
    , "Invoice Lines / Label"
    , "Invoice Lines / Account"
    , "Invoice Lines / Quantity"
    , "Invoice Lines / Consolidated Qty"
    , "Invoice Lines / Unit Price"
    , "Invoice Lines / Discount (%)"
    , "Invoice Lines / Taxes"
FROM (
	SELECT 
		'__import__.account.move_' || ai.id AS "External ID"
		, wb.code AS "Company"
		, ai.division AS "Division"
		, rp.default_code AS "Partner"
		, ai.origin AS "Reference"
		, ai.supplier_invoice_number AS "Supplier Invoice Number"
		, ai.date_invoice AS "Invoice/Bill Date"
		, ai.document_date AS "Date"
		, LPAD(SPLIT_PART(ap.name, '/', 2)::INT::TEXT, 2, '0') || '/' || SPLIT_PART(ap.name, '/', 1) AS "Period / Database ID"
		, ai.reference AS "Payment Reference"
		, ai.partner_bank_id AS "Recipient Bank"
		, ai.date_due AS "Due Date"
		, apt.name AS "Payment Terms"
		, aj.name AS "Journal"
		, ai.pajak_gabungan AS "Combined Tax?"
        -- , ai.discount_cash AS "Discount Lines / Discount Cash"
        -- , ai.discount_program AS "Discount Lines / Discount Program"
        -- , ai.discount_lain AS "Discount Lines / Discount Other"
		, '__import__.account.move.line_' || ail.id AS "Invoice Lines / External ID"
		, wbl.code AS "Invoice Lines / Company"
        -- , ail.product_id AS "Invoice Lines / Product"
		, '[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')' AS "Invoice Lines / Product / Database ID"
		, '__import__.purchase.order.line_' || ail.purchase_line_id AS "Invoice lines / Purchase Order Line / External ID"
		, ail.name AS "Invoice Lines / Label"
		, aa.name AS "Invoice Lines / Account"
		, ail.quantity AS "Invoice Lines / Quantity"
		, ail.consolidated_qty AS "Invoice Lines / Consolidated Qty"
		, ail.price_unit AS "Invoice Lines / Unit Price"
		, ail.discount AS "Invoice Lines / Discount (%)"
		, REGEXP_REPLACE(ait.name, '[()]', '', 'g') AS "Invoice Lines / Taxes"
		, ROW_NUMBER() OVER (PARTITION BY ai.number ORDER BY ail.id) AS rn
	FROM account_invoice ai 
    LEFT JOIN account_invoice_line ail ON ail.invoice_id = ai.id
	LEFT JOIN wtc_branch wb ON ai.branch_id = wb.id
	LEFT JOIN res_partner rp ON ai.partner_id = rp.id
	LEFT JOIN account_period ap ON ai.period_id = ap.id
	LEFT JOIN account_payment_term apt ON ai.payment_term = apt.id
	LEFT JOIN account_journal aj ON ai.journal_id = aj.id
	LEFT JOIN account_invoice_tax ait ON ait.invoice_id = ai.id
	LEFT JOIN wtc_branch wbl ON ail.branch_id = wbl.id
	LEFT JOIN product_product pp ON ail.product_id = pp.id
	LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
	LEFT JOIN product_attribute_value_product_product_rel pavpp ON pavpp.prod_id = pp.id
	LEFT JOIN product_attribute_value pav ON pavpp.att_id = pav.id
	LEFT JOIN account_account aa ON ail.account_id = aa.id
	JOIN ir_model im ON ai.model_id = im.id AND im.model = 'purchase.order'
	WHERE 1=1
	AND ai.type = 'in_invoice'
	AND ai.state NOT IN ('cancel', 'paid')
    -- optional filter
	-- AND ai.division = 'Unit'
	-- AND wb.code = 'DDS'
	-- AND ai.id = 22636107
) t;

--1 (Get Product)
SELECT
	prod.id
FROM product_product prod
LEFT JOIN product_template prod_tmpl ON prod_tmpl.id = prod.product_tmpl_id
LEFT JOIN product_variant_combination variant ON prod.id = variant.product_product_id
LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
LEFT JOIN product_category prod_categ ON prod_tmpl.categ_id = prod_categ.id
WHERE 1=1
AND prod_tmpl.division = 'Unit' -- fill from "Division" PO Invoice Query TEDS
AND '[' || prod_tmpl.default_code || '] ' || COALESCE(prod_tmpl.name ->> 'en_US', prod_tmpl.description ->> 'en_US') || ' (' || (attr_value.name ->> 'en_US') || ')' ILIKE '%[MRB] SCOOPY FASHION (BLACK)%'; -- fill from "Invoice Lines / Product / Database ID" PO Invoice Query TEDS

--2 (Get Period)
SELECT
	tap.id
FROM tw_account_period tap
LEFT JOIN res_company rc ON tap.company_id = rc.id
WHERE 1=1
AND rc.code = 'DDS' -- fill from "Company" PO Invoice Query TEDS
AND tap.name = '04/2026'; -- fill from "Period / Database ID" PO Invoice Query TEDS