-- Unit dan Sparepart
SELECT
    '__import__.tw.p2p.config_' || wpc.id AS "External ID"
    , rp.name AS "Supplier"
    , wpc.tentative_1 AS "Tentative 1 (%)"
    , wpc.tentative_2 AS "Tentative 2 (%)"
    , TRUE AS "Active"
FROM wtc_p2p_config wpc
LEFT JOIN res_partner rp ON wpc.supplier_id = rp.id
WHERE 1=1;