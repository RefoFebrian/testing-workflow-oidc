--location Area
SELECT
    'stock_location_' || sla.name::varchar || '_' || sla.id::varchar AS "External ID",
    'MML' AS "company_id",
    'internal' AS usage,
    True AS active,
    0 AS capacity,
    sla.description AS description,
    sla.name AS name,
    'WH-MML/Stock' AS "location_id"
FROM dms_stockcard_location_area sla

--location line
SELECT
    'stock_location_' || sla.name::varchar || '.' || sll.name::varchar || '_' || sll.id::varchar AS "External ID",
    'MML' AS "company_id",
    'internal' AS usage,
    True AS active,
    0 AS capacity,
    sll.name AS description,
    sll.name AS name,
    'stock_location_' || sla.name::varchar || '_' || sla.id::varchar AS "location_id/id"
FROM dms_stockcard_location_line sll
LEFT JOIN dms_stockcard_location_area sla ON sla.id = sll.area_id

--location rack
SELECT
    'stock_location_' || sla.name::varchar || '.' || sll.name::varchar || '.' || slr.name::varchar || '_' || slr.id::varchar AS "External ID",
    'MML' AS "company_id",
    'internal' AS usage,
    True AS active,
    0 AS capacity,
    slr.name AS description,
    slr.name AS name,
    'stock_location_' || sla.name::varchar || '.' || sll.name::varchar || '_' || sll.id::varchar AS "location_id/id"
FROM dms_stockcard_location_rack slr
LEFT JOIN dms_stockcard_location_line sll ON sll.id = slr.line_id
LEFT JOIN dms_stockcard_location_area sla ON sla.id = sll.area_id

--location container
SELECT
    'stock_location_' || sla.name::varchar || '.' || sll.name::varchar || '.' || slr.name::varchar || '.' || slc.name::varchar || '_' || slc.id::varchar AS "External ID",
    'MML' AS "company_id",
    'internal' AS usage,
    True AS active,
    0 AS capacity,
    slc.name AS description,
    slc.name AS name,
    'stock_location_' || sla.name::varchar || '.' || sll.name::varchar || '.' || slr.name::varchar || '_' || slr.id::varchar AS "location_id/id"
FROM dms_stockcard_location_container slc
LEFT JOIN dms_stockcard_location_rack slr ON slr.id = slc.rack_id
LEFT JOIN dms_stockcard_location_line sll ON sll.id = slr.line_id
LEFT JOIN dms_stockcard_location_area sla ON sla.id = sll.area_id

--location binbox
SELECT
    'stock_location_' || slb.name::varchar || '_' || slb.id::varchar AS "External ID",
    'MML' AS "company_id",
    'internal' AS usage,
    slb.lokasi_aktif AS active,
    COALESCE(slb.lokasi_sementara,False) AS is_temporary_location,
    CASE
        WHEN slb.capacity <= 0 THEN NULL
        ELSE slb.capacity
    END AS capacity,
    slb.name AS description,
    slb.binbox AS name,
    'stock_location_' || sla.name::varchar || '.' || sll.name::varchar || '.' || slr.name::varchar || '.' || slc.name::varchar || '_' || slc.id::varchar AS "location_id/id",
    INITCAP(slb.division) AS division,
    CASE
    	WHEN slb.division = 'unit' AND slb.capacity > 0 THEN True
    	ELSE False 
    END AS is_restrict_capacity,
    CASE 
        WHEN slb.tipe_lokasi = 'ng' THEN 'tw_stock.tw_select_stock_loc_type_nrfs'
        WHEN slb.tipe_lokasi = 'hotline' THEN 'tw_stock.tw_select_stock_loc_type_hotline'
        ELSE 'tw_stock.tw_select_stock_loc_type_rfs'
    END AS "type_id/id"
FROM dms_stockcard_location_binbox slb
LEFT JOIN dms_stockcard_location_container slc ON slc.id = slb.container_id
LEFT JOIN dms_stockcard_location_rack slr ON slr.id = slc.rack_id
LEFT JOIN dms_stockcard_location_line sll ON sll.id = slr.line_id
LEFT JOIN dms_stockcard_location_area sla ON sla.id = sll.area_id
