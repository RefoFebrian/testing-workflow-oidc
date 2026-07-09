SELECT
    'tw_kpb_engine_type_' ||
    LOWER(
        CONCAT_WS(
            '_',
            wket.engine_no,
            REPLACE(wket.name, ' ', '_')
        )
    ) AS "External ID",
    CASE
        WHEN wkep.id IS NOT NULL THEN
            'tw_kpb_engine_price_' ||
            LOWER(
                CONCAT_WS(
                    '_',
                    wket.engine_no,
                    REPLACE(wket.name, ' ', '_'),
                    wkep.kpb_ke
                )
            )
        ELSE
            NULL
    END AS "Kategori Nilai Mesin/External ID",
    wket.engine_no,
    wket.name,
    wkep.kpb_ke,
    wkep.jasa,
    wkep.oli
FROM wtc_kpb_engine_type wket
LEFT JOIN wtc_kpb_engine_price wkep
    ON wkep.kategori_id = wket.id
ORDER BY
    CASE
        WHEN wket.id IS NULL THEN 1
        ELSE 0
    END,
    wket.engine_no ASC