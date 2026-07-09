-- SKEMA 1
-- Sales Program Subsidi Barang
SELECT 
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Area" END AS "Area"
    , CASE WHEN rn = 1 THEN "Name" END AS "Name"
    , CASE WHEN rn = 1 THEN "Product" END AS "Product"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Kode Program MD" END AS "Kode Program MD"
    , CASE WHEN rn = 1 THEN "Tipe Sales Program" END AS "Tipe Sales Program"
    , CASE WHEN rn = 1 THEN "Active" END AS "Active"
    , CASE WHEN rn = 1 THEN "Keterangan" END AS "Keterangan"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
    , "Sales Program Lines / External ID"
    , "Sales Program Lines / Product"
	, "Sales Program Lines / Qty"
	, "Sales Program Lines / Diskon AHM"
	, "Sales Program Lines / Diskon MD"
	, "Sales Program Lines / Diskon Dealer"
	, "Sales Program Lines / Diskon Finco"
FROM (
    SELECT 
        '__import__.tw.sales.program_psb_' || wsb.id AS "External ID"
        , wb.code AS "Branch"
        , wsb.division AS "Division"
        , wa.description AS "Area"
        , wsb.name AS "Name"
        , pp.name_template AS "Product"
        , TO_CHAR(wsb.date_start, 'YYYY-MM-DD') AS "Start Date"
        , TO_CHAR(wsb.date_end, 'YYYY-MM-DD') AS "End Date"
        , wsb.partner_ref AS "Kode Program MD"
        , 'Program Subsidi Barang' AS "Tipe Sales Program"
        , wsb.active AS "Active"
        , wsb.keterangan AS "Keterangan"
        , CASE
            WHEN wsb.state = 'draft' THEN 'Draft'
            WHEN wsb.state = 'waiting_for_approval' THEN 'Waiting For Approval'
            WHEN wsb.state = 'approved' THEN 'Approved'
            WHEN wsb.state = 'rejected' THEN 'Rejected'
            WHEN wsb.state = 'editable' THEN 'Editable'
            WHEN wsb.state = 'on_revision' THEN 'On Revision'
        ELSE NULL END AS "State"
        , '__import__.tw.sales.program.line_psb_' || wsbl.id AS "Sales Program Lines / External ID"
        , pt.name AS "Sales Program Lines / Product"
        , wsbl.qty AS "Sales Program Lines / Qty"
        , wsbl.diskon_ahm AS "Sales Program Lines / Diskon AHM"
        , wsbl.diskon_md AS "Sales Program Lines / Diskon MD"
        , wsbl.diskon_dealer AS "Sales Program Lines / Diskon Dealer"
        , wsbl.diskon_finco AS "Sales Program Lines / Diskon Finco"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program_psb_' || wsb.id ORDER BY wsbl.id) AS rn
    FROM wtc_subsidi_barang wsb
    LEFT JOIN wtc_subsidi_barang_line wsbl ON wsbl.subsidi_barang_id = wsb.id
    LEFT JOIN product_product pp ON wsb.product_template_id = pp.id
    LEFT JOIN wtc_branch wb ON wsb.branch_id = wb.id
    LEFT JOIN wtc_area wa ON wsb.area_id = wa.id
    LEFT JOIN product_template pt ON wsbl.product_id = pt.id
    WHERE 1=1
    AND wsb.active IS TRUE
    AND wsb.date_end >= NOW()
    AND wsbl.total_diskon > 0
) data
WHERE 1=1;

-- SKEMA 2
-- Sales Program Subsidi Barang (HEADER)
SELECT 
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Division" END AS "Division"
    , CASE WHEN rn = 1 THEN "Area" END AS "Area"
    , CASE WHEN rn = 1 THEN "Name" END AS "Name"
    , CASE WHEN rn = 1 THEN "Product" END AS "Product"
    , CASE WHEN rn = 1 THEN "Start Date" END AS "Start Date"
    , CASE WHEN rn = 1 THEN "End Date" END AS "End Date"
    , CASE WHEN rn = 1 THEN "Kode Program MD" END AS "Kode Program MD"
    , CASE WHEN rn = 1 THEN "Tipe Sales Program" END AS "Tipe Sales Program"
    , CASE WHEN rn = 1 THEN "Active" END AS "Active"
    , CASE WHEN rn = 1 THEN "Keterangan" END AS "Keterangan"
    , CASE WHEN rn = 1 THEN "State" END AS "State"
FROM (
    SELECT 
        '__import__.tw.sales.program_psb_' || wsb.id AS "External ID"
        , wb.code AS "Branch"
        , wsb.division AS "Division"
        , wa.description AS "Area"
        , wsb.name AS "Name"
        , pp.name_template AS "Product"
        , TO_CHAR(wsb.date_start, 'YYYY-MM-DD') AS "Start Date"
        , TO_CHAR(wsb.date_end, 'YYYY-MM-DD') AS "End Date"
        , wsb.partner_ref AS "Kode Program MD"
        , 'Program Subsidi Barang' AS "Tipe Sales Program"
        , wsb.active AS "Active"
        , wsb.keterangan AS "Keterangan"
        , CASE
            WHEN wsb.state = 'draft' THEN 'Draft'
            WHEN wsb.state = 'waiting_for_approval' THEN 'Waiting For Approval'
            WHEN wsb.state = 'approved' THEN 'Approved'
            WHEN wsb.state = 'rejected' THEN 'Rejected'
            WHEN wsb.state = 'editable' THEN 'Editable'
            WHEN wsb.state = 'on_revision' THEN 'On Revision'
        ELSE NULL END AS "State"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program_psb_' || wsb.id ORDER BY wsb.id) AS rn
    FROM wtc_subsidi_barang wsb
    LEFT JOIN product_product pp ON wsb.product_template_id = pp.id
    LEFT JOIN wtc_branch wb ON wsb.branch_id = wb.id
    LEFT JOIN wtc_area wa ON wsb.area_id = wa.id
    WHERE 1=1
    AND wsb.active IS TRUE
    AND wsb.date_end >= NOW()
) data
WHERE 1=1;

-- Sales Program Subsidi Barang (LINE)
SELECT
    CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Sales Program Lines / External ID" END AS "Sales Program Lines / External ID"
    , CASE WHEN rn = 1 THEN "Sales Program Lines / Product" END AS "Sales Program Lines / Product"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Qty" END AS "Sales Program Lines / Qty"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon AHM" END AS "Sales Program Lines / Diskon AHM"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon MD" END AS "Sales Program Lines / Diskon MD"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon Dealer" END AS "Sales Program Lines / Diskon Dealer"
	, CASE WHEN rn = 1 THEN "Sales Program Lines / Diskon Finco" END AS "Sales Program Lines / Diskon Finco"
FROM (
    SELECT 
        '__import__.tw.sales.program_psb_' || wsb.id AS "External ID"
        , '__import__.tw.sales.program.line_psb_' || wsbl.id AS "Sales Program Lines / External ID"
        , pt.name AS "Sales Program Lines / Product"
        , wsbl.qty AS "Sales Program Lines / Qty"
        , wsbl.diskon_ahm AS "Sales Program Lines / Diskon AHM"
        , wsbl.diskon_md AS "Sales Program Lines / Diskon MD"
        , wsbl.diskon_dealer AS "Sales Program Lines / Diskon Dealer"
        , wsbl.diskon_finco AS "Sales Program Lines / Diskon Finco"
        , ROW_NUMBER() OVER (PARTITION BY '__import__.tw.sales.program.line_psb_' || wsbl.id ORDER BY wsbl.id) AS rn
    FROM wtc_subsidi_barang_line wsbl
    LEFT JOIN wtc_subsidi_barang wsb ON wsbl.subsidi_barang_id = wsb.id
    LEFT JOIN product_template pt ON wsbl.product_id = pt.id
    WHERE 1=1
    AND wsb.active IS TRUE
    AND wsb.date_end >= NOW()
    AND wsbl.total_diskon > 0
) data
WHERE 1=1;