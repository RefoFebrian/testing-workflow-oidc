SELECT
    'stock_location_' || sl.id AS "External ID",
    wb.code AS "company_id",
    CASE 
        WHEN sl."usage" IN ('nrfs', 'procurement') THEN 'internal'
        ELSE sl."usage" 
    END AS usage,
    sl.active,
    sl.loc_barcode AS barcode,
    sl.maximum_qty AS capacity,
    sl.posx,
    REPLACE(sl.description, ',', '.') AS description,
    sl.start_date AS effective_start_date,
    sl.end_date AS effective_end_date,
    sl.posz,
    sl.scrap_location,
    REPLACE(sl.name, ',', '.') AS name,
    sl.is_approval,
    CASE
        WHEN parent_location.complete_name ILIKE 'Physical Locations%' 
            THEN 'WH-' || REGEXP_REPLACE(
                            REGEXP_REPLACE(parent_location.complete_name, '^Physical Locations\s*/\s*', ''), 
                            '\s*/\s*', 
                            '/', 
                            'g'
                        )
        WHEN parent_location.complete_name ILIKE 'Partner Location%' 
            THEN REGEXP_REPLACE(
                    parent_location.complete_name,
                    '^Partner Location',
                    'Partner'
                )
        ELSE parent_location.complete_name
    END AS "location_id",
    pr.name AS removal_strategy_id,
    CASE 
        WHEN sl.maximum_qty IS NOT NULL AND sl.maximum_qty > 0 THEN TRUE 
        ELSE NULL
    END AS is_restrict_capacity,
    sl.posy,
    CASE 
        WHEN sl.jenis = 'gudang_unit' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_gudang_unit'
        WHEN sl.jenis = 'channel_permis_noviardi' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_cpn'
        WHEN sl.jenis = 'pos' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_pos'
        WHEN sl.jenis = 'channel' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_channel'
        WHEN sl.jenis = 'canvasing' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_canvasing'
        WHEN sl.jenis = 'showroom' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_showroom'
        WHEN sl.jenis = 'pameran' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_pameran'
        WHEN sl.jenis = 'roadshow' THEN 'tw_stock_location_btl.tw_select_stock_loc_type_btl_roadshow'
        ELSE NULL
    END AS "btl_loc_type_id/id",
    CASE 
        WHEN sl.USAGE = 'internal' AND sl.jenis IN ('gudang_unit', 'canvasing', 'showroom', 'pameran', 'channel') THEN 'tw_stock.tw_select_stock_loc_type_event'
        WHEN sl.USAGE = 'internal' THEN 'tw_stock.tw_select_stock_loc_type_rfs'
        WHEN sl.USAGE IN ('inventory', 'nrfs', 'production') THEN 'tw_stock.tw_select_stock_loc_type_nrfs'
        ELSE NULL
    END AS "type_id/id"
FROM stock_location sl
LEFT JOIN wtc_branch wb ON wb.id = sl.branch_id 
LEFT JOIN stock_location parent_location ON parent_location.id = sl.location_id 
LEFT JOIN product_removal pr ON pr.id = sl.removal_strategy_id 
LEFT JOIN stock_warehouse sw ON sw.id = sl.warehouse_id
WHERE sl."usage" IN ('internal', 'nrfs') AND sl.name != 'Stock'
AND sl."branch_id" is not null