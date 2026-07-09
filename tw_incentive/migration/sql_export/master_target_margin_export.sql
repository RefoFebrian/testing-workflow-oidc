SELECT
	CASE WHEN rn = 1 THEN "External ID" END AS "External ID"
    , CASE WHEN rn = 1 THEN "Branch" END AS "Branch"
    , CASE WHEN rn = 1 THEN "Job" END AS "Job"
    , CASE WHEN rn = 1 THEN "Active Date" END AS "Active Date"
    , CASE WHEN rn = 1 THEN "Status" END AS "Status"
    , "Target Margin Line / External ID"
    , "Target Margin Line / Series"
	, "Target Margin Line / Cash"
	, "Target Margin Line / Credit"
FROM (
	SELECT
		'__import__.tw.master.target.margin_' || dmtm.id AS "External ID"
		, rb.kode_dealer as "Branch"
		, dmtm.job as "Job"
		, TO_CHAR(dmtm.date + interval '7 hours', 'YYYY-MM-DD HH24:MI:SS') as "Active Date"
		, dmtm.state AS "Status"
		, '__import__.tw.master.target.margin.line_' || mtml.id AS "Target Margin Line / External ID"
		, dps.name AS "Target Margin Line / Series"
		, mtml.cash AS "Target Margin Line / Cash"
		, mtml.credit AS "Target Margin Line / Credit"
		, ROW_NUMBER() OVER (PARTITION BY '__import__.tw.master.target.margin_' || dmtm.id ORDER BY mtml.id) AS rn
	FROM dms_master_target_margin dmtm
	LEFT JOIN master_target_margin_line mtml ON mtml.target_margin_id = dmtm.id
	LEFT JOIN res_branch rb ON dmtm.branch_id = rb.id
	LEFT JOIN dms_product_series dps ON mtml.series_id = dps.id
	WHERE 1=1
	AND dmtm.job IS NOT NULL
) data
WHERE 1=1;