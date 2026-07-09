-- Kelurahan
SELECT
    wk.name AS kelurahan,
    wk.code AS code,
    wk.zip AS zip_code,
    wkc.code AS kecamatan,
    wc.code AS kab_kota,
    rcs.code AS provinsi,
    '' AS sequence
FROM wtc_kelurahan wk
LEFT JOIN wtc_kecamatan wkc ON wk.kecamatan_id = wkc.id
LEFT JOIN wtc_city wc ON wkc.city_id = wc.id
LEFT JOIN res_country_state rcs ON wc.state_id = rcs.id
WHERE wk.code IS NOT null
  AND wk.code ~ '^[0-9]+$'
  AND TRIM(wk.code) <> '';