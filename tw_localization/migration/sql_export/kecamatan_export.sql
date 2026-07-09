-- Kecamatan
SELECT
	wk.code AS code,
	wk.name AS kecamatan,
	wc.code AS city,
	rcs.code AS provinsi,
	'' AS sequence
FROM wtc_kecamatan wk
LEFT JOIN wtc_city wc ON wk.city_id = wc.id
LEFT JOIN res_country_state rcs ON wc.state_id = rcs.id
WHERE wk.code IS NOT NULL
  AND TRIM(wk.code) <> ''
  AND wk.code ~ '^[0-9]+$';