-- Master Bank
SELECT
	'__import__.res.bank_' || rb.id AS "External ID"
	, rb.name AS "Name"
	, rb.code AS "Code"
	, rb.code AS "3 Digit Code"
	, rb.bic AS "Bank Identifier Code"
FROM res_bank rb
WHERE 1=1
AND rb.active IS TRUE;