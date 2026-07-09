SELECT 
	dbk."name" AS "Category", 
	dbk.sub_kategori_id ,
	UPPER(hj."name")||' RETAIL' AS "Job",
	'Hari (H)' AS "Unit",
	dbte.eskalasi_ke AS "Interval",
	dbte.jam_eskalasi AS "Eskalasi Jam",
	dbte.menit_eskalasi AS "Eskalasi Menit"
FROM dms_boom_task_eskalasi dbte 
LEFT JOIN dms_boom_kategori dbk ON dbk.id = dbte.kategori_id 
LEFT JOIN hr_job hj ON hj.id = dbte.job_id 
WHERE 1=1
ORDER BY dbk.name asc