SELECT 
	'tw_petty_cash_type_' || REPLACE(wprt.name::varchar,' ','_') || '_' || wprt.id::varchar as external_id,
	wprt.name as name,
	wprt.active as active,
	tprtl.name as "petty_cash_type_lines/name",
	account.code as "petty_cash_type_lines/account_id"
FROM wtc_payments_request_type wprt
LEFT JOIN teds_payments_request_type_line tprtl ON tprtl.type_id = wprt.id
LEFT JOIN account_account account ON account.id = tprtl.account_id
WHERE wprt.type = 'PCO'