-- import master area
SELECT
    '__import__.res.area_' || wba.tipe_area || '_' || wba.id "External ID"
    , wba.name "Name"
    , wba.name "Code"
    , wba.name "Description"
FROM wtc_branch_area wba
WHERE 1=1;

-- import master branch area
SELECT
	'__import__.tw.branch.setting_' || wb.id "External ID"
    , wb.name branch_name
    , wb.code branch_code
	, '__import__.res.area_' || wba1.tipe_area || '_' || wba1.id "Area 1 / External ID"
	, '__import__.res.area_' || wba2.tipe_area || '_' || wba2.id "Area 2 / External ID"
FROM wtc_branch wb
LEFT JOIN wtc_branch_area wba1 ON wb.branch_area_1 = wba1.id
LEFT JOIN wtc_branch_area wba2 ON wb.branch_area_2 = wba2.id
WHERE 1=1
AND (wb.branch_area_1 IS NOT NULL OR wb.branch_area_2 IS NOT NULL);