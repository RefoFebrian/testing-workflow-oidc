--Master Discount Cash
SELECT
	'tw_sale_discount_cash_' || LOWER(wpot.name) || '-' || tmdc.id AS "External ID",
	'Sparepart|' || wpot.name AS "Type",
	apt.name AS "Payment Term",
	tmdc.discount_plus AS "Discount %"
FROM teds_master_discount_cash tmdc 
LEFT JOIN wtc_purchase_order_type wpot ON wpot.id = tmdc.type_id 
LEFT JOIN account_payment_term apt ON apt.id = tmdc.payment_term_id 