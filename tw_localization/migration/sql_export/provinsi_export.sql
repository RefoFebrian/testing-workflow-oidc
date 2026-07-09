-- Provinsi
SELECT
	rcs.name,
	rcs.code,
	rc.name AS country
FROM res_country_state rcs
LEFT JOIN res_country rc ON rcs.country_id = rc.id
where rc.name = 'Indonesia'