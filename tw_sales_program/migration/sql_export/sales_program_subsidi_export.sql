-- SKEMA 1
-- Sales Program Subsidi
SELECT 
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Area" END AS "Area"
    , CASE WHEN rn = 1 THEN "Name" END AS "Name"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Kode Program MD" END AS "Kode Program MD"
    , CASE WHEN rn = 1 THEN "Tipe Subsidi" END AS "Tipe Subsidi"
    , CASE WHEN rn = 1 THEN "Finco" END AS "Finco"
    , CASE WHEN rn = 1 THEN "Tipe Sales Program" END AS "Tipe Sales Program"
    , CASE WHEN rn = 1 THEN "Active" END AS "Active"
    , CASE WHEN rn = 1 THEN "Keterangan" END AS "Keterangan"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
    , "Sales Program Lines / External ID"
    , "Sales Program Lines / Product"
	, "Sales Program Lines / Tipe DP"
	, "Sales Program Lines / DP Minimal"
	, "Sales Program Lines / Diskon AHM"
	, "Sales Program Lines / Diskon MD"
	, "Sales Program Lines / Diskon Dealer"
	, "Sales Program Lines / Diskon Finco"
FROM (
    SELECT 
        '__import__.tw.sales.program_ps_' || wps.id AS "External ID"
        , wb.code AS "Branch"
        , wps.division AS "Division"
        , wa.description AS "Area"
        , wps.name AS "Name"
        , TO_CHAR(wps.date_start, 'YYYY-MM-DD') AS "Start Date"
        , TO_CHAR(wps.date_end, 'YYYY-MM-DD') AS "End Date"
        , wps.partner_ref AS "Kode Program MD"
        , CASE
            WHEN wps.tipe_subsidi = 'fix' THEN 'Fix'
            WHEN wps.tipe_subsidi = 'non' THEN 'Non Fix'
        ELSE NULL END AS "Tipe Subsidi"
        , rp.name AS "Finco"
        , 'Program Subsidi' AS "Tipe Sales Program"
        , wps.active AS "Active"
        , wps.keterangan AS "Keterangan"
        , CASE
            WHEN wps.state = 'draft' THEN 'Draft'
            WHEN wps.state = 'waiting_for_approval' THEN 'Waiting For Approval'
            WHEN wps.state = 'approved' THEN 'Approved'
            WHEN wps.state = 'rejected' THEN 'Rejected'
            WHEN wps.state = 'editable' THEN 'Editable'
            WHEN wps.state = 'on_revision' THEN 'On Revision'
        ELSE NULL END AS "State"
        , '__import__.tw.sales.program.line_ps_' || wpsl.id AS "Sales Program Lines / External ID"
        , pt.name AS "Sales Program Lines / Product"
        , wpsl.tipe_dp AS "Sales Program Lines / Tipe DP"
        , wpsl.amount_dp AS "Sales Program Lines / DP Minimal"
        , wpsl.diskon_ahm AS "Sales Program Lines / Diskon AHM"
        , wpsl.diskon_md AS "Sales Program Lines / Diskon MD"
        , wpsl.diskon_dealer AS "Sales Program Lines / Diskon Dealer"
        , wpsl.diskon_finco AS "Sales Program Lines / Diskon Finco"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program_ps_' || wps.id ORDER BY wpsl.id) AS rn
    FROM wtc_program_subsidi wps
    LEFT JOIN wtc_program_subsidi_line wpsl ON wpsl.program_subsidi_id = wps.id
    LEFT JOIN wtc_branch wb ON wps.branch_id = wb.id
    LEFT JOIN wtc_area wa ON wps.area_id = wa.id
    LEFT JOIN res_partner rp ON wps.instansi_id = rp.id
    LEFT JOIN product_template pt ON wpsl.product_template_id = pt.id
    WHERE 1=1
    AND wps.active IS TRUE
    AND wps.date_end >= NOW()
    AND wpsl.total_diskon > 0
) data
WHERE 1=1;

-- SKEMA 2
-- Sales Program Subsidi (HEADER)
SELECT
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Area" END AS "Area"
    , CASE WHEN rn = 1 THEN "Name" END AS "Name"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Kode Program MD" END AS "Kode Program MD"
    , CASE WHEN rn = 1 THEN "Tipe Subsidi" END AS "Tipe Subsidi"
    , CASE WHEN rn = 1 THEN "Finco" END AS "Finco"
    , CASE WHEN rn = 1 THEN "Tipe Sales Program" END AS "Tipe Sales Program"
    , CASE WHEN rn = 1 THEN "Active" END AS "Active"
    , CASE WHEN rn = 1 THEN "Keterangan" END AS "Keterangan"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
FROM (
    SELECT 
        '__import__.tw.sales.program_ps_' || wps.id AS "External ID"
        , wb.code AS "Branch"
        , wps.division AS "Division"
        , wa.description AS "Area"
        , wps.name AS "Name"
        , TO_CHAR(wps.date_start, 'YYYY-MM-DD') AS "Start Date"
        , TO_CHAR(wps.date_end, 'YYYY-MM-DD') AS "End Date"
        , wps.partner_ref AS "Kode Program MD"
        , CASE
            WHEN wps.tipe_subsidi = 'fix' THEN 'Fix'
            WHEN wps.tipe_subsidi = 'non' THEN 'Non Fix'
        ELSE NULL END AS "Tipe Subsidi"
        , rp.name AS "Finco"
        , 'Program Subsidi' AS "Tipe Sales Program"
        , wps.active AS "Active"
        , wps.keterangan AS "Keterangan"
        , CASE
            WHEN wps.state = 'draft' THEN 'Draft'
            WHEN wps.state = 'waiting_for_approval' THEN 'Waiting For Approval'
            WHEN wps.state = 'approved' THEN 'Approved'
            WHEN wps.state = 'rejected' THEN 'Rejected'
            WHEN wps.state = 'editable' THEN 'Editable'
            WHEN wps.state = 'on_revision' THEN 'On Revision'
        ELSE NULL END AS "State"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program_ps_' || wps.id ORDER BY wps.id) AS rn
    FROM wtc_program_subsidi wps
    LEFT JOIN wtc_branch wb ON wps.branch_id = wb.id
    LEFT JOIN wtc_area wa ON wps.area_id = wa.id
    LEFT JOIN res_partner rp ON wps.instansi_id = rp.id
    WHERE 1=1
    AND wps.active IS TRUE
    AND wps.date_end >= NOW()
) data
WHERE 1=1;

-- Sales Program Subsidi (LINE)
SELECT 
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Sales Program Lines / External ID" END AS "Sales Program Lines / External ID"
    , CASE WHEN rn = 1 THEN "Sales Program Lines / Product" END AS "Sales Program Lines / Product"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Tipe DP" END AS "Sales Program Lines / Tipe DP"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / DP Minimal" END AS "Sales Program Lines / DP Minimal"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon AHM" END AS "Sales Program Lines / Diskon AHM"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon MD" END AS "Sales Program Lines / Diskon MD"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon Dealer" END AS "Sales Program Lines / Diskon Dealer"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon Finco" END AS "Sales Program Lines / Diskon Finco"
FROM (
    SELECT 
        '__import__.tw.sales.program_ps_' || wps.id AS "External ID"
        , '__import__.tw.sales.program.line_ps_' || wpsl.id AS "Sales Program Lines / External ID"
        , pt.name AS "Sales Program Lines / Product"
        , wpsl.tipe_dp AS "Sales Program Lines / Tipe DP"
        , wpsl.amount_dp AS "Sales Program Lines / DP Minimal"
        , wpsl.diskon_ahm AS "Sales Program Lines / Diskon AHM"
        , wpsl.diskon_md AS "Sales Program Lines / Diskon MD"
        , wpsl.diskon_dealer AS "Sales Program Lines / Diskon Dealer"
        , wpsl.diskon_finco AS "Sales Program Lines / Diskon Finco"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program.line_ps_' || wpsl.id ORDER BY wpsl.id) AS rn
    FROM wtc_program_subsidi_line wpsl
    LEFT JOIN wtc_program_subsidi wps ON wpsl.program_subsidi_id = wps.id
    LEFT JOIN product_template pt ON wpsl.product_template_id = pt.id
    WHERE 1=1
    AND wps.active IS TRUE
    AND wps.date_end >= NOW()
    AND wpsl.total_diskon > 0
) data
WHERE 1=1;