-- MIGRATION MASTER GROUP DEALER
SELECT 
	'tw_master_dealer_group_' || id AS "External ID",
	name AS "Name"
FROM teds_master_groups_dealer tmgd 