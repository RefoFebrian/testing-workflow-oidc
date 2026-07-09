SELECT
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Sales Category" END AS "Sales Category"
    , CASE WHEN rn = 1 THEN "Branch Class" END AS "Branch Class"
    , CASE WHEN rn = 1 THEN "Status" END AS "Status"
    , "Incentive Line / External ID"
    , "Incentive Line / Quantity"
	, "Incentive Line / Cash"
	, "Incentive Line / Accumulate Cash"
	, "Incentive Line / Credit"
	, "Incentive Line / Accumulate Credit"
	, "Incentive Line / Reward"
FROM (
	SELECT
		'__import__.tw.master.incentive_' || dmi.id AS "External ID"
		, CASE
			WHEN dmi.sales_category = 'sales_koordinator' THEN 'sales_coordinator'
			ELSE dmi.sales_category
		END AS "Sales Category"
		, dmi.branch_category AS "Branch Class"
		, dmi.state AS "Status"
		, '__import__.tw.master.incentive.line_' || mil.id AS "Incentive Line / External ID"
		, mil.qty AS "Incentive Line / Quantity"
		, mil.cash AS "Incentive Line / Cash"
		, mil.credit AS "Incentive Line / Credit"
		, mil.reward AS "Incentive Line / Reward"
		, ROW_NUMBER() OVER (PARTITION BY '__import__.tw.master.incentive_' || dmi.id ORDER BY mil.id) AS rn
	FROM dms_master_insentif dmi
	LEFT JOIN master_insentif_line mil ON mil.insentif_id = dmi.id
	WHERE 1=1
) data
WHERE 1=1;