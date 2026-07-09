-- Register Kwitansi
SELECT
    CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Date" END AS "Date"
    , CASE WHEN rn = 1 THEN "Is E-Kwitansi?" END AS "Is E-Kwitansi?"
    , CASE WHEN rn = 1 THEN "Nomor Awal" END AS "Nomor Awal"
    , CASE WHEN rn = 1 THEN "Nomor Akhir" END AS "Nomor Akhir"
    , CASE WHEN rn = 1 THEN "Prefix" END AS "Prefix"
    , CASE WHEN rn = 1 THEN "Padding" END AS "Padding"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
    , "Kwitansi / External ID"
    , "Kwitansi / No. Register"
    , "Kwitansi / Branch"
    , "Kwitansi / State"
FROM (
	SELECT
		'__import__.tw.register.kwitansi_' || wrk.id AS "External ID"
		, wb.name AS "Branch"
		, wrk.date AS "Date"
		, wrk.is_ekwitansi AS "Is E-Kwitansi?"
		, wrk.nomor_awal AS "Nomor Awal"
		, wrk.nomor_akhir AS "Nomor Akhir"
		, wrk.prefix AS "Prefix"
		, wrk.padding AS "Padding"
		, wrk.state AS "State"
		, '__import__.tw.register.kwitansi.line_' || wrkl.id AS "Kwitansi / External ID"
		, wrkl.name AS "Kwitansi / No. Register"
		, wb.name AS "Kwitansi / Branch"
		, wrkl.state AS "Kwitansi / State"
		, ROW_NUMBER() OVER (PARTITION BY '__import__.tw.register.kwitansi_' || wrk.id ORDER BY wrkl.id) AS rn
	FROM wtc_register_kwitansi wrk
	LEFT JOIN wtc_register_kwitansi_line wrkl ON wrkl.register_kwitansi_id = wrk.id
	LEFT JOIN wtc_branch wb ON wrk.branch_id = wb.id
	WHERE 1=1
	AND wrk.state = 'posted'
	AND wrkl.state = 'open'
	AND wrkl.new_payment_id IS NULL
) data
WHERE 1=1;

-- header
SELECT
    '__import__.tw.register.kwitansi_' || wrk.id AS "External ID"
    , wb.name AS "Branch"
    , wrk.date AS "Date"
    , wrk.is_ekwitansi AS "Is E-Kwitansi?"
    , wrk.nomor_awal AS "Nomor Awal"
    , wrk.nomor_akhir AS "Nomor Akhir"
    , wrk.prefix AS "Prefix"
    , wrk.padding AS "Padding"
    , wrk.state AS "State"
FROM wtc_register_kwitansi wrk
LEFT JOIN wtc_branch wb ON wrk.branch_id = wb.id
WHERE 1=1
AND wrk.state = 'posted';

-- line
SELECT
    '__import__.tw.register.kwitansi.line_' || wrkl.id AS "External ID"
    , wrkl.name AS "No. Register"
    , wb.name AS "Branch"
    , wrkl.state AS "State"
    , '__import__.tw.register.kwitansi_' || wrk.id AS "Register Kwitansi / External ID"
FROM wtc_register_kwitansi wrk
LEFT JOIN wtc_register_kwitansi_line wrkl ON wrkl.register_kwitansi_id = wrk.id
LEFT JOIN wtc_branch wb ON wrk.branch_id = wb.id
WHERE 1=1
AND wrk.state = 'posted'
AND wrkl.state = 'open'
AND wrkl.new_payment_id IS NULL;