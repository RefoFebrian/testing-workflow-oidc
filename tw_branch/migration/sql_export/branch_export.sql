--Branch
SELECT
	'tw_branch_'||lower(wb.code) AS "External ID",
	'PT Tunas Dwipa Matra' AS "Parent Company",
	wb.name AS company_name,
    wb.code AS code,
    wb.ahm_code AS atpm_code,
    wb.profit_centre AS profit_centre,
    rp.default_code AS principle,
	CASE
	    WHEN wb.branch_type = 'DL' THEN 'tw_branch.tw_selection_branch_type_dl'
	    WHEN wb.branch_type = 'MD' THEN 'tw_branch.tw_selection_branch_type_md'
	    WHEN wb.branch_type = 'HO' THEN 'tw_branch.tw_selection_branch_type_ho'
	    ELSE wb.branch_type
	END AS "Branch Type / External ID",
	wb.tgl_kukuh AS tanggal_kukuh,
	wb.street,
	wb.street2,
	wc.code AS kabupaten,
	wc.name AS city,
	rcs.code AS state,
	wk.zip AS zip_code,
	wkc.code AS kecamatan,
	wk.code AS kelurahan,
	wb.rt,
	wb.rw,
	regexp_replace(wb.npwp, '[^0-9]', '', 'g') AS npwp,
	CASE
        WHEN wb.is_allow_lead THEN 'TRUE'
        ELSE 'FALSE'
    END AS allow_auto_deal_lead,
    wb.phone,
	CASE
		WHEN wb.mobile ILIKE '8%' THEN '+628' || SUBSTRING(wb.mobile FROM 2)
	    WHEN wb.mobile ILIKE '08%' THEN '+628' || SUBSTRING(wb.mobile FROM 3)
	    WHEN wb.mobile ILIKE '+628%' THEN wb.mobile
	    WHEN wb.mobile ILIKE '628%%' THEN '+628' || SUBSTRING(wb.mobile FROM 4)
	    ELSE wb.mobile
	END AS mobile,
    wb.email
FROM wtc_branch wb
LEFT JOIN res_partner rp ON rp.id = wb.default_supplier_id
LEFT JOIN wtc_city wc ON wc.id = wb.city_id
LEFT JOIN res_country_state rcs ON rcs.id = wb.state_id
LEFT JOIN wtc_kelurahan wk ON wk.id = wb.zip_code_id
LEFT JOIN wtc_kecamatan wkc ON wkc.id = wb.kecamatan_id
LEFT JOIN stock_warehouse sw ON sw.id = wb.warehouse_id
WHERE wb.code NOT IN ('MML','HHO')