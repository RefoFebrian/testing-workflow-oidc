SELECT 
	'tw_cash_count_validation_' || REPLACE(tccv.name::varchar,' ','_') || '_' || tccv.id::varchar as external_id,
	tccv.name as name,
	tccv.type as type,
	tccv.note as note
FROM teds_cash_count_validasi tccv