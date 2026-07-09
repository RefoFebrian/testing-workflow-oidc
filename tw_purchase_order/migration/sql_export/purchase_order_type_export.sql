-- Master Purchase Order Type Unit
SELECT
	'__import__.tw.purchase.order.type_' || wpot.id AS "External ID"
	, wpot.category AS "Division"
	, wpot.name AS "Name"
	, CASE
		WHEN wpot.category = 'Unit' THEN 'Immediate Payment'
		ELSE NULL
	END AS "Payment Terms"
	, wpot.date_start AS "Start Date" 
	, wpot.date_end AS "End Date"
FROM wtc_purchase_order_type wpot 
WHERE 1=1
AND wpot.category = 'Unit';

-- Master Purchase Order Type Sparepart
SELECT
	'__import__.tw.purchase.order.type_' || wpot.id AS "External ID"
	, wpot.category AS "Division"
	, wpot.name AS "Name"
	, CASE
		WHEN wpot.category = 'Unit' THEN 'Immediate Payment'
		ELSE NULL
	END AS "Payment Terms"
	, wpot.date_start AS "Start Date" 
	, wpot.date_end AS "End Date"
FROM wtc_purchase_order_type wpot 
WHERE 1=1
AND wpot.category = 'Sparepart';