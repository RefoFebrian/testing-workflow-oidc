WITH activity_line_sequenced AS (
    SELECT 
        tspal.*,
        ROW_NUMBER() OVER (
            PARTITION BY tspal.activity_id 
            ORDER BY tspal.id
        ) AS rn
    FROM teds_sales_plan_activity_line tspal
)
SELECT 
    -- Header (Plan Activity) - Only populated on the first detail line (rn = 1)
	CASE WHEN line.rn = 1 THEN 'tw_activity_atl_btl_'||lower(wb.code)||'_'||tspa.id ELSE '' END AS  "External ID",
    CASE WHEN line.rn = 1 THEN wb.code ELSE '' END AS "Branch",
    CASE WHEN line.rn = 1 THEN tspa.bulan ELSE '' END AS "Month",
    CASE WHEN line.rn = 1 THEN tspa.tahun::text ELSE '' END AS "Year",
    CASE WHEN line.rn = 1 THEN tspa.state ELSE '' END AS "State",
    -- Detail (Activity Line)
    line.state AS "Detail / State",
    CASE
        WHEN line.jaringan_penjualan IS NOT NULL THEN 'SalesChannel|' || line.jaringan_penjualan
        ELSE ''
    END AS "Detail / Jaringan Penjualan",
    tat.name AS "Detail / Activity Type",
    tk.name AS "Detail / Titik Keramaian",
    line.jenis_pengajuan AS "Detail / Submission Type",
    line.no_telp AS "Detail / No Telp",
    kel.name AS "Detail / Kelurahan",
    line.street AS "Detail / Street",
    line.rt AS "Detail / RT",
    line.rw AS "Detail / RW",
    line.start_date AS "Detail / Start Date",
    line.end_date AS "Detail / End Date",
    sl.name AS "Detail / Location",
    sl.name AS "Detail / Activity Name",
    sl.start_date AS "Detail / Rent Start Date",
    sl.end_date AS "Detail / Rent End Date",
    pic.nip AS "Detail / PIC",
    line.display_unit AS "Detail / Display Unit",
    line.target_unit AS "Detail / Target Unit",
    line.target_customer AS "Detail / Target Customer"
FROM teds_sales_plan_activity tspa
LEFT JOIN wtc_branch wb ON wb.id = tspa.branch_id
INNER JOIN activity_line_sequenced line ON tspa.id = line.activity_id
LEFT JOIN stock_location sl ON sl.id = line.location_id 
LEFT JOIN teds_act_type_sumber_penjualan tat ON tat.id = line.act_type_id
LEFT JOIN titik_keramaian tk ON tk.id = line.titik_keramaian_id
LEFT JOIN wtc_kelurahan kel ON kel.id = line.kelurahan_id
LEFT JOIN hr_employee pic ON pic.id = line.pic_id
WHERE 1=1
ORDER BY tspa.id, line.rn;