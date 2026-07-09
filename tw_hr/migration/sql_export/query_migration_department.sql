select distinct
	hd."name" as "Department Name"
from hr_department hd
left join hr_employee he on he.id = hd.manager_id
where 1=1