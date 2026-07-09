-- SKEMA 1
-- Sales Program Voucher
SELECT
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Name" END AS "Name"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Tipe Sales Program" END AS "Tipe Sales Program"
    , CASE WHEN rn = 1 THEN "Active" END AS "Active"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
    , "Sales Program Lines / External ID"
    , "Sales Program Lines / Product"
    , "Sales Program Lines / Diskon Others"
FROM (
    SELECT 
        '__import__.tw.sales.program_pv_' || tmpv.id AS "External ID"
        , wb.code AS "Branch"
        , tmpv.division AS "Division"
        , tmpv.name AS "Name"
        , TO_CHAR(tmpv.start_date, 'YYYY-MM-DD') AS "Start Date"
        , TO_CHAR(tmpv.end_date, 'YYYY-MM-DD') AS "End Date"
        , 'Program Voucher' AS "Tipe Sales Program"
        , tmpv.is_active AS "Active"
        , CASE
            WHEN tmpv.state = 'draft' THEN 'Draft'
            WHEN tmpv.state = 'waiting_for_approval' THEN 'Waiting For Approval'
            WHEN tmpv.state = 'approved' THEN 'Approved'
            WHEN tmpv.state = 'rejected' THEN 'Rejected'
            WHEN tmpv.state = 'editable' THEN 'Editable'
            WHEN tmpv.state = 'on_revision' THEN 'On Revision'
        ELSE NULL END AS "State"
        , '__import__.tw.sales.program.line_pv_' || tmpvl.id AS "Sales Program Lines / External ID"
        , pt.name AS "Sales Program Lines / Product"
        , tmpvl.diskon_voucher AS "Sales Program Lines / Diskon Others"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program_pv_' || tmpv.id ORDER BY tmpvl.id) AS rn
    FROM teds_master_program_voucher tmpv
    LEFT JOIN teds_master_program_voucher_line tmpvl ON tmpvl.voucher_id = tmpv.id
    LEFT JOIN wtc_branch wb ON tmpv.branch_id = wb.id
    LEFT JOIN product_template pt ON tmpvl.product_tmpl_id = pt.id
    WHERE 1=1
    AND tmpv.is_active IS TRUE
    AND tmpv.end_date >= NOW()
	AND tmpvl.diskon_voucher > 0
) data
WHERE 1=1;

-- SKEMA 2
-- Sales Program Voucher (HEADER)
SELECT 
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Name" END AS "Name"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Tipe Sales Program" END AS "Tipe Sales Program"
    , CASE WHEN rn = 1 THEN "Active" END AS "Active"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
FROM (
    SELECT 
        '__import__.tw.sales.program_pv_' || tmpv.id AS "External ID"
        , wb.code AS "Branch"
        , tmpv.division AS "Division"
        , tmpv.name AS "Name"
        , TO_CHAR(tmpv.start_date, 'YYYY-MM-DD') AS "Start Date"
        , TO_CHAR(tmpv.end_date, 'YYYY-MM-DD') AS "End Date"
        , 'Program Voucher' AS "Tipe Sales Program"
        , tmpv.is_active AS "Active"
        , CASE
            WHEN tmpv.state = 'draft' THEN 'Draft'
            WHEN tmpv.state = 'waiting_for_approval' THEN 'Waiting For Approval'
            WHEN tmpv.state = 'approved' THEN 'Approved'
            WHEN tmpv.state = 'rejected' THEN 'Rejected'
            WHEN tmpv.state = 'editable' THEN 'Editable'
            WHEN tmpv.state = 'on_revision' THEN 'On Revision'
        ELSE NULL END AS "State"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program_pv_' || tmpv.id ORDER BY tmpv.id) AS rn
    FROM teds_master_program_voucher tmpv
    LEFT JOIN wtc_branch wb ON tmpv.branch_id = wb.id
    WHERE 1=1
    AND tmpv.is_active IS TRUE
    AND tmpv.end_date >= NOW()
) data
WHERE 1=1;

-- Sales Program Voucher (LINE)
SELECT
    CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Sales Program Lines / External ID" END AS "Sales Program Lines / External ID"
    , CASE WHEN rn = 1 THEN "Sales Program Lines / Product" END AS "Sales Program Lines / Product"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon Others" END AS "Sales Program Lines / Diskon Others"
FROM (
    SELECT 
        '__import__.tw.sales.program_pv_' || tmpv.id AS "External ID"
        , '__import__.tw.sales.program.line_pv_' || tmpvl.id AS "Sales Program Lines / External ID"
        , pt.name AS "Sales Program Lines / Product"
        , tmpvl.diskon_voucher AS "Sales Program Lines / Diskon Others"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program.line_pv_' || tmpvl.id ORDER BY tmpvl.id) AS rn
    FROM teds_master_program_voucher_line tmpvl
    LEFT JOIN teds_master_program_voucher tmpv ON tmpvl.voucher_id = tmpv.id
    LEFT JOIN product_template pt ON tmpvl.product_tmpl_id = pt.id
    WHERE 1=1
    AND tmpv.is_active IS TRUE
    AND tmpv.end_date >= NOW()
	AND tmpvl.diskon_voucher > 0
) data
WHERE 1=1;