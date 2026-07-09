-- Master Area
SELECT
	"External ID"
	, "Name"
	, "Code"
	, "Description"
	, "Branch"
FROM (
	SELECT
		'__import__.res.area_' || wa.id "External ID"
		, wa.description "Name"
		, wa.code "Code"
		, wa.description "Description"
		, ARRAY_TO_STRING(ARRAY_AGG(DISTINCT TRIM(REGEXP_REPLACE(wb.code, '^[^-]*-', ''))), ',') "Branch"
	FROM wtc_area wa 
	LEFT JOIN wtc_area_cabang_rel wacr ON wacr.area_id = wa.id
	LEFT JOIN wtc_branch wb ON wacr.branch_id = wb.id
	WHERE 1=1
	GROUP BY wa.id
) data
WHERE 1=1

-- Master Branch Area
SELECT 
	'__import__.res_area_' || REPLACE(area.tipe_area::varchar,' ','_') || '_' || REPLACE(area.name::varchar,' ','_') as external_id,
	area.name as name,
	REPLACE(area.tipe_area::varchar,'_',' ') || ' ' || area.name::varchar as code,
	area.name as description
FROM wtc_branch_area area