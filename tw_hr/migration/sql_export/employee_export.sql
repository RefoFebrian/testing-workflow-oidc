-- Employee
SELECT
	he.name_related,
	he.nip ,
    wb.code AS branch,
    wa.description AS area,
	CASE
	    WHEN he.work_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
	    THEN he.work_email
	    ELSE NULL
	END AS work_email,
    CASE WHEN LENGTH(regexp_replace(he.work_phone, '[^0-9]', '', 'g')) > 8 THEN
    	CASE
		    WHEN he.work_phone LIKE '0%' 
		    THEN '62' || SUBSTRING(regexp_replace(he.work_phone, '[^0-9]', '', 'g') FROM 2)
		    ELSE regexp_replace(he.work_phone, '[^0-9]', '', 'g')
		END 
	ELSE '' END AS work_phone,
	CASE
	    WHEN he.mobile_phone LIKE '0%' 
	    THEN '62' || SUBSTRING(regexp_replace(he.mobile_phone, '[^0-9]', '', 'g') FROM 2)
	    ELSE he.mobile_phone
	END AS work_mobile,
    hj.name AS job_position,
    '' AS tags,
    hc.name_related AS coach,
    hm.name_related AS manager,
    he.tgl_masuk AS working_start_date,
    he.tgl_keluar AS working_end_date,
    REGEXP_REPLACE(he.npwp, '[^0-9]', '', 'g') AS no_npwp,
    he.no_kontrak,
    'PT Tunas Dwipa Matra' AS work_address,
    he.street AS private_street,
    he.street2 AS private_street2,
    rcs.code AS private_state,
    wc.name AS private_city,
    wk.zip AS private_zip,
    'Indonesia' AS private_country,
    he.email AS private_email,
    COALESCE(INITCAP(he.marital),'Single') AS marital_status,
    rc.name AS nationality_country,
    he.identification_id AS identification_no,
    he.passport_id AS passport_no,
    INITCAP(he.gender) AS gender,
    he.birthday AS date_of_birth,
    he.user,
    he.no_rekening AS nomor_rekening,
    he.name_related AS nama_pemilik_rekening,
	UPPER (he.bank) as bank
FROM hr_employee he
LEFT JOIN hr_job hj ON he.job_id = hj.id
LEFT JOIN wtc_branch wb ON he.branch_id = wb.id
LEFT JOIN wtc_area wa ON he.area_id = wa.id
LEFT JOIN employee_category_rel ecr ON he.id = ecr.emp_id
LEFT JOIN hr_employee_category hec ON ecr.category_id = hec.id
LEFT JOIN hr_department hd  ON he.department_id = hd.id
LEFT JOIN hr_employee hc ON he.coach_id = hc.id
LEFT JOIN hr_employee hm ON he.parent_id = hm.id
LEFT JOIN res_partner rp ON he.address_id = rp.id
LEFT JOIN res_country_state rcs ON he.state_id = rcs.id
LEFT JOIN wtc_city wc ON he.city_id = wc.id
LEFT JOIN wtc_kelurahan wk ON he.zip_id = wk.id
LEFT JOIN res_country rc ON he.country_id = rc.id
WHERE he.tgl_keluar IS NULL
AND he.nip IS NOT null
AND hj.name IN ('SALES COUNTER PARTNER',
'TEAM LEADER PARTNER',
'Team Leader Partner Digital',
'SALESMAN PARTNER')