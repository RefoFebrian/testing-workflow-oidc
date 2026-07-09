-- Kabupaten/Kota
SELECT
	wc.code AS code,
	wc.name AS kab_kota,
	rcs.code AS provinsi,
	'' AS sequence
FROM wtc_city wc
LEFT JOIN res_country_state rcs ON wc.state_id = rcs.id
WHERE wc.code IS NOT null
  AND wc.code ~ '^[0-9]+$'
  AND TRIM(wc.code) <> '';