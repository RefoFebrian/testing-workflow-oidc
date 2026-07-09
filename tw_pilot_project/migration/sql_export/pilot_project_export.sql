-- MIGRATION PILOT PROJECT
SELECT 
    'tw_pilot_project_' || tpp.id AS "External ID",
    tpp.name AS "Name",
    tpp.description AS "Description",
    'Tuple' AS "Output Type",
    string_agg('tw_branch_' || lower(wb.code), ',') AS "branch_ids"
FROM teds_pilot_project tpp
LEFT JOIN teds_pilot_branches tpb ON tpb.pilot_id = tpp.id
LEFT JOIN wtc_branch wb ON wb.id = tpb.branch_id
WHERE tpp.is_active IS TRUE
GROUP BY tpp.id, tpp.name, tpp.description
ORDER BY tpp.id;