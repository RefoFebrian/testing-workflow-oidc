--Pricelist BBN
SELECT
    REPLACE(whb.name, ',', ' ') AS pricelist_name,
    CASE
        WHEN whb.active THEN 'TRUE'
        ELSE 'FALSE'
    END AS active,
    '' AS company,
    'BBN Purchase' AS pricelist_type,
    'All Branch' AS area,
    rp.name AS agency
FROM wtc_harga_bbn whb
LEFT JOIN wtc_harga_birojasa whbj ON whbj.harga_bbn_id = whb.id
LEFT JOIN res_partner rp ON rp.id = whbj.birojasa_id
WHERE whb.active = true
GROUP BY whb.name, whb.active, rp.name
ORDER BY whb.name, rp.name;