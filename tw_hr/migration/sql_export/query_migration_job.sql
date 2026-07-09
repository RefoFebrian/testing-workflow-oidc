SELECT DISTINCT 
	hj."name" AS "Job Position", 
	CASE
		WHEN hd.name = 'ADMINISTRASI' THEN 'ADMINISTRATION'
		WHEN hd."name" = 'Human Resource Department Head Office' THEN 'HRD HO'
		WHEN hd.name = 'FINANCE' THEN 'FINANCE AND ADMINISTRATION'
		ELSE hd.name
	END as "Department",
	'SalesForce|'||CASE 
		WHEN hj.sales_force = 'sales_koordinator' THEN 'sales_coordinator'
		WHEN hj.sales_force = 'soh' THEN 'sales_operation_head'
		WHEN hj.sales_force = 'AM' THEN 'area_manager'
		ELSE hj.sales_force 
	END AS "Sales Force"
FROM hr_job hj 
JOIN hr_department hd ON hd.id = hj.department_id
WHERE 1=1