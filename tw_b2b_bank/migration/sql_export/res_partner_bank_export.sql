SELECT
	'__import__.res.partner.bank_' || tbbmb.id AS "External ID"
	, tbbac.name AS "Bank"
	, tbbmb.name AS "Account Number"
	, wb.name AS "Account Holder Name"
	, tbbmb.name AS "Code"
	, wb.name AS "Account Holder"
	, tbbmb.plafon AS "Plafon"
	, tbbmb.currency AS "Currency"
	, tbbmb.is_fetch_statement AS "Fetch Statement"
	, TO_CHAR(tbbmb.last_balance_check + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') AS "Last Balance Check"
	, TO_CHAR(tbbmb.last_fetch + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') AS "Last Fetch"
	, wb.name AS "Branch"
	, tbbac.name AS "API Configuration / Database ID"
	, aa.code || ' - ' || aa.name AS "Account"
	, tbbas.name AS "Schedule"
	, tbbmb.float_amount AS "Float Amount"
	, tbbmb.hold_amount AS "Hold Amount"
	, tbbmb.available_balance AS "Available Balance"
	, tbbmb.balance AS "Balance"
	, TRUE AS "Allow Send Money?"
FROM teds_b2b_master_bank tbbmb
LEFT JOIN wtc_branch wb ON tbbmb.branch_id = wb.id
LEFT JOIN account_account aa ON tbbmb.account_id = aa.id
LEFT JOIN teds_b2b_api_config tbbac ON tbbmb.config_id = tbbac.id
LEFT JOIN teds_b2b_api_schedule tbbas ON tbbmb.schedule_id = tbbas.id
WHERE 1=1;

--1 (Get API Configuration / Database ID)
SELECT
	tac.id
FROM tw_api_configuration tac 
LEFT JOIN tw_selection ts ON tac.api_type_id = ts.id AND ts.type = 'ApiType'
WHERE 1=1
AND ts.value IN ('bca', 'bri'); -- fill from "API Configuration / Database ID" B2B Master Bank Query TEDS