SELECT
    '__import__.tw.p2p.periode_' || wpp.id AS "External ID"
    , wpp.name AS "Name"
    , wpp.start_date AS "Effective Start Date"
    , wpp.end_date AS "Effective End Date"
    , wpp.periode_start_date AS "Periode Start Date"
    , wpp.periode_end_date AS "Periode End Date"
    , TRUE AS "Active"
FROM wtc_p2p_periode wpp
WHERE 1=1;