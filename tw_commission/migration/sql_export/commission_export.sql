-- MIGRATION MASTER HUTANG KOMISI
SELECT 
    'tw_commission_' || whk.id AS "External ID",
    'tw_branch_' || lower(wb.code) AS "branch_id/id",
    whk.division AS "Division",
    wa.code AS "Area",
    whk.name AS "Name",
    TO_CHAR(whk.date_start, 'YYYY-MM-DD') AS "Date Start",
    TO_CHAR(whk.date_end, 'YYYY-MM-DD') AS "Date End",
    whk.tipe_komisi AS "Tipe Komisi",
    'tw_commission_' || whk.id || '_line_' || whkl.id AS "hutang_komisi_line/id",
    pt.name AS "hutang_komisi_line/product_template_id/code",
    whkl.amount AS "hutang_komisi_line/amount"
FROM wtc_hutang_komisi whk
LEFT JOIN wtc_branch wb ON wb.id = whk.branch_id
LEFT JOIN wtc_area wa ON wa.id = wb.area_id
LEFT JOIN wtc_hutang_komisi_line whkl ON whkl.hutang_komisi_id = whk.id
LEFT JOIN product_template pt ON pt.id = whkl.product_template_id
WHERE whk.active IS TRUE
  AND whk.date_start <= CURRENT_DATE
  AND (whk.date_end IS NULL OR whk.date_end >= CURRENT_DATE)
ORDER BY whk.id, whkl.id;