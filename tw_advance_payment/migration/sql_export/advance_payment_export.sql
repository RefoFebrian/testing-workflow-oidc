SELECT
	'__import__.tw.advance.payment_' || wap.id AS "External ID"
	, wb.name AS "Branch"
	, wap.division AS "Division"
	, INITCAP(he.name_related) AS "Employee"
	, wap.date_due AS "Due Date"
	, wap.amount AS "Amount"
	, wap.date AS "Date"
	, '''' || rpba.account_number AS "Rekening Penerima / Database ID"
	, aj.name AS "Journal"
	, wap.email AS "Email"
	, balance_adv_payment.balance AS "Balance"
	, NULL AS "Proposal"
	, wap.description AS "Description"
	, 'confirm' AS "State"
FROM wtc_advance_payment wap
LEFT JOIN wtc_branch wb ON wap.branch_id = wb.id
LEFT JOIN hr_employee he ON wap.employee_id = he.id
LEFT JOIN res_partner_bank_account rpba ON wap.partner_bank_id = rpba.id
LEFT JOIN res_bank rb ON rpba.bank_id = rb.id
LEFT JOIN LATERAL (
	SELECT
		id
	FROM wtc_settlement ws
	WHERE 1=1
	AND ws.advance_payment_id = wap.id
	LIMIT 1
) settlement ON TRUE
LEFT JOIN account_journal aj ON wap.payment_method = aj.id
LEFT JOIN (
	SELECT
		wap2.employee_id
		, SUM(wap2.amount) balance
	FROM wtc_advance_payment wap2
	WHERE 1=1
	AND wap2.state = 'confirmed'
	GROUP BY wap2.employee_id
) balance_adv_payment ON balance_adv_payment.employee_id = wap.employee_id
WHERE 1=1
AND settlement.id IS NULL
AND wap.state = 'confirmed';

--1 (Get Rekening Penerima / Database ID)
SELECT
	rpb.id
FROM res_partner_bank rpb
WHERE 1=1
AND rpb.acc_number IN (''); -- fill from "Rekening Penerima / Database ID" Advance Payment Transaction Query TEDS