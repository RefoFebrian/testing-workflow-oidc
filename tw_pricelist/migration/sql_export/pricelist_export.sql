-- Pricelist
SELECT
    pp.name AS pricelist_name,
    CASE
        WHEN pp.active THEN 'TRUE'
        ELSE 'FALSE'
    END AS active,
    '' AS company,
    CASE
        WHEN pp.type IN ('sale_bbn_hitam', 'sale_bbn_merah') THEN 'BBN Sales'
        WHEN pp.type = 'sale' THEN 'Sales'
        WHEN pp.type = 'purchase' THEN 'Purchase'
        ELSE pp.type
    END AS pricelist_type,
    '' AS area,
    CASE
        WHEN pp.type = 'sale_bbn_hitam' THEN 'Hitam'
        WHEN pp.type = 'sale_bbn_merah' THEN 'Merah'
        ELSE ''
    END AS plate,
    '' AS agency
FROM product_pricelist pp
ORDER BY pp.name;

-----------------------------------------------------------------
-----------------------------------------------------------------
--------------------------- PRICELIST ---------------------------
-----------------------------------------------------------------
-----------------------------------------------------------------

-- Pricelist Unit Active
select
	'__export__.product_pricelist_' || pp.id as xml_id,
    pp.name AS pricelist_name,
    CASE
        WHEN pp.active THEN 'TRUE'
        ELSE 'FALSE'
    END AS active,
    '' AS company,
    CASE
        WHEN pp.type IN ('sale_bbn_hitam', 'sale_bbn_merah') THEN 'BBN Sales'
        WHEN pp.type = 'sale' THEN 'Sales'
        WHEN pp.type = 'purchase' THEN 'Purchase'
        ELSE pp.type
    END AS pricelist_type,
    '' AS area,
    CASE
        WHEN pp.type = 'sale_bbn_hitam' THEN 'Hitam'
        WHEN pp.type = 'sale_bbn_merah' THEN 'Merah'
        ELSE ''
    END AS plate,
    '' AS agency
FROM product_pricelist pp
where pp.active = true
and id in (
	select
		distinct(ppv.pricelist_id )
	FROM product_pricelist_version ppv
	LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
	where pp.id in (
		SELECT DISTINCT id
		FROM (
		    SELECT
		        pp.id
		    FROM product_pricelist pp
		    INNER JOIN wtc_branch wb 
		        ON wb.pricelist_unit_sales_id = pp.id or (wb.pricelist_unit_sales_id isnull and pp.name ilike '%%unit%%')
		        OR wb.pricelist_unit_purchase_id = pp.id or (wb.pricelist_unit_purchase_id isnull and pp.name ilike '%%unit%%')
		    WHERE pp.active = true
		) AS subquery
	)
	and ppv.date_end >= '2026-05-06'
)

-- Pricelist BBN Jual Active
select
	'__export__.product_pricelist_' || pp.id as xml_id,
    pp.name AS pricelist_name,
    CASE
        WHEN pp.active THEN 'TRUE'
        ELSE 'FALSE'
    END AS active,
    '' AS company,
    CASE
        WHEN pp.type IN ('sale_bbn_hitam', 'sale_bbn_merah') THEN 'BBN Sales'
        WHEN pp.type = 'sale' THEN 'Sales'
        WHEN pp.type = 'purchase' THEN 'Purchase'
        ELSE pp.type
    END AS pricelist_type,
    '' AS area,
    CASE
        WHEN pp.type = 'sale_bbn_hitam' THEN 'Hitam'
        WHEN pp.type = 'sale_bbn_merah' THEN 'Merah'
        ELSE ''
    END AS plate,
    '' AS agency
FROM product_pricelist pp
where pp.active = true
and id in (
	select
		distinct(ppv.pricelist_id )
	FROM product_pricelist_version ppv
	LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
	where pp.id in (
		SELECT DISTINCT id
		FROM (
		    SELECT
		        pp.id
		    FROM product_pricelist pp
		    INNER JOIN wtc_branch wb 
		        ON wb.pricelist_bbn_hitam_id = pp.id or (wb.pricelist_bbn_hitam_id isnull and pp.name ilike '%%bbn%%')
		        OR wb.pricelist_bbn_merah_id = pp.id or (wb.pricelist_bbn_merah_id isnull and pp.name ilike '%%bbn%%')
		    WHERE pp.active = true
		) AS subquery
	)
	and ppv.date_end >= '2026-05-18'
)
ORDER BY pp.name;

-- Pricelist BBN Beli Active
SELECT
    'product_pricelist_' || pp.id AS external_id,
    pp.name AS pricelist_name,
    CASE
        WHEN pp.active THEN 'TRUE'
        ELSE 'FALSE'
    END AS active,
    '' AS company,
    'BBN Purchase' AS pricelist_type,
    '' AS area,
    CASE
        WHEN ppv.tipe_plat = 'H' THEN 'Hitam'
        WHEN ppv.tipe_plat = 'M' THEN 'Merah'
        ELSE ''
    END AS plate,
    '' AS agency
FROM wtc_harga_bbn pp
LEFT JOIN wtc_harga_bbn_line ppv 
    ON ppv.bbn_id = pp.id
WHERE pp.active = TRUE
AND ppv.end_date >= '2026-05-18'
GROUP BY
    pp.id,
    pp.name,
    pp.active,
    ppv.tipe_plat
ORDER BY pp.name, plate;

-- Pricelist Sparepart
select
	'__export__.product_pricelist_' || pp.id as xml_id,
    pp.name AS pricelist_name,
    CASE
        WHEN pp.active THEN 'TRUE'
        ELSE 'FALSE'
    END AS active,
    '' AS company,
    CASE
        WHEN pp.type IN ('sale_bbn_hitam', 'sale_bbn_merah') THEN 'BBN Sales'
        WHEN pp.type = 'sale' THEN 'Sales'
        WHEN pp.type = 'purchase' THEN 'Purchase'
        ELSE pp.type
    END AS pricelist_type,
    '' AS area,
    CASE
        WHEN pp.type = 'sale_bbn_hitam' THEN 'Hitam'
        WHEN pp.type = 'sale_bbn_merah' THEN 'Merah'
        ELSE ''
    END AS plate,
    '' AS agency
FROM product_pricelist pp
where pp.active = true
and id in (
	select
		distinct(ppv.pricelist_id )
	FROM product_pricelist_version ppv
	LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
	where pp.id in (
		SELECT DISTINCT id
		FROM (
		    SELECT
		        pp.id
		    FROM product_pricelist pp
		    INNER JOIN wtc_branch wb 
		        ON wb.pricelist_part_sales_id = pp.id or (wb.pricelist_part_sales_id isnull and pp.name ilike '%%part%%')
		        OR wb.pricelist_part_purchase_id = pp.id or (wb.pricelist_part_purchase_id isnull and pp.name ilike '%%part%%')
		    WHERE pp.active = true
		) AS subquery
	)
	and ppv.date_end >= '2026-05-06'
)

-----------------------------------------------------------------
-----------------------------------------------------------------
----------------------- PRICELIST VERSION -----------------------
-----------------------------------------------------------------
-----------------------------------------------------------------


-- Pricelist Version Unit Active
select
	'tw_product_pricelist_version_' || ppv.id as xml_id,
    ppv.name AS name,
    '' AS area,
    TO_CHAR(ppv.date_start,'YYYY-MM-DD') AS start_date,
    TO_CHAR(ppv.date_end,'YYYY-MM-DD') AS end_date,
    pp.name AS price_list,
    'Active' AS state
FROM product_pricelist_version ppv
LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
where pp.id in (
	SELECT DISTINCT id
	FROM (
	    SELECT
	        pp.id
	    FROM product_pricelist pp
	    INNER JOIN wtc_branch wb 
	        ON wb.pricelist_unit_sales_id = pp.id or (wb.pricelist_unit_sales_id isnull and pp.name ilike '%%unit%%')
	        OR wb.pricelist_unit_purchase_id = pp.id or (wb.pricelist_unit_purchase_id isnull and pp.name ilike '%%unit%%')
	    WHERE pp.active = true
	) AS subquery
)
and ppv.date_end >= '2026-05-06'

-- Pricelist Version BBN Active
select
	'tw_product_pricelist_version_' || ppv.id as xml_id,
    ppv.name AS name,
    '' AS area,
    TO_CHAR(ppv.date_start,'YYYY-MM-DD') AS start_date,
    TO_CHAR(ppv.date_end,'YYYY-MM-DD') AS end_date,
    pp.name AS price_list,
    'Active' AS state
FROM product_pricelist_version ppv
LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
where pp.id in (
	SELECT DISTINCT id
	FROM (
	    SELECT
	        pp.id
	    FROM product_pricelist pp
	    INNER JOIN wtc_branch wb 
	        ON wb.pricelist_bbn_hitam_id = pp.id or (wb.pricelist_bbn_hitam_id isnull and pp.name ilike '%%bbn%%')
	        OR wb.pricelist_bbn_merah_id = pp.id or (wb.pricelist_bbn_merah_id isnull and pp.name ilike '%%bbn%%')
	    WHERE pp.active = true
	) AS subquery
)
and ppv.date_end >= '2026-05-06'

-- Pricelist Version BBN Beli Active
select
	'tw_product_pricelist_version_' || ppv.id as external_id,
    ppv.name AS name,
    '' AS area,
    TO_CHAR(ppv.start_date,'YYYY-MM-DD') AS start_date,
    TO_CHAR(ppv.end_date,'YYYY-MM-DD') AS end_date,
    pp.name AS price_list,
    CASE
        WHEN tipe_plat = 'H' THEN 'Hitam'
        WHEN tipe_plat = 'M' THEN 'Merah'
        ELSE tipe_plat
    END AS tipe_plat,
    'Active' AS state
FROM wtc_harga_bbn_line ppv
LEFT JOIN wtc_harga_bbn pp ON pp.id = ppv.bbn_id
where ppv.end_date >= '2026-05-18'
and ppv.active = true

-- Pricelist Version Sparepart Active
select
	'tw_product_pricelist_version_' || ppv.id as xml_id,
    ppv.name AS name,
    '' AS area,
    TO_CHAR(ppv.date_start,'YYYY-MM-DD') AS start_date,
    TO_CHAR(ppv.date_end,'YYYY-MM-DD') AS end_date,
    pp.name AS price_list,
    'Active' AS state
FROM product_pricelist_version ppv
LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
where pp.id in (
	SELECT DISTINCT id
	FROM (
	    SELECT
	        pp.id
	    FROM product_pricelist pp
	    INNER JOIN wtc_branch wb 
	        ON wb.pricelist_part_sales_id = pp.id or (wb.pricelist_part_sales_id isnull and pp.name ilike '%%part%%')
	        OR wb.pricelist_part_purchase_id = pp.id or (wb.pricelist_part_purchase_id isnull and pp.name ilike '%%part%%')
	    WHERE pp.active = true
	) AS subquery
)
and ppv.date_end >= '2026-05-06'


----------------------------------------------------------
----------------------------------------------------------
--------------------- PRICELIST ITEM ---------------------
----------------------------------------------------------
----------------------------------------------------------


-- Pricelist Item Unit
select
	'tw_product_pricelist_item_' || lower(ppv.name) || '_' || lower(coalesce(
		CASE
		    WHEN ppi.categ_id IS NOT NULL THEN
		        concat_ws('_', pt.name, pav.code)
		    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
		        concat_ws('_', pt.name, pav.code)
		    ELSE
		        concat_ws('_', ppi.name::TEXT, pav.code)
		end, '')
	) as external_id,
    CASE
        WHEN ppi.categ_id IS NOT NULL THEN 'Category'
        ELSE 'Product'
    END AS display_applied_on,
    COALESCE(pc3.name || ' / ', '') ||
    COALESCE(pc2.name || ' / ', '') ||
    COALESCE(pc.name, '') AS category,
    CASE
	    WHEN ppi.categ_id IS NOT NULL THEN
	        concat_ws('|', pt.name, pav.code)
	    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
	        concat_ws('|', pt.name, pav.code)
	    ELSE
	        concat_ws('|', ppi.name::TEXT, pav.code)
	END as product_var_code,
	CASE
	    WHEN ppi.categ_id IS NOT NULL THEN
	        pt.name
	    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
	        pt.name
	    ELSE
	        ppi.name
	END as product,
	pav.code as attribute_code,
	pav.name as attribute_name,
    CASE
        WHEN pp_v.id IS NOT NULL THEN
            COALESCE(pt_direct.name, '')
        ELSE ''
    END AS variant,
    CASE
        WHEN ppi.base = -1 THEN 'Formula'
        WHEN ppi.base = 1 THEN 'Fixed Price'
        ELSE ''
    END AS compute_price,
    ppi.min_quantity AS min_quantity,
    ppv.name AS pricelist_version,
    pp.name AS pricelist,
    ppv.date_start AS start_date,
    ppv.date_end AS end_date,
    CASE
        WHEN ppi.base = 1 THEN 'Sales Price'
        WHEN ppi.base = -1 THEN 'Other Pricelist'
        ELSE ''
    END AS based_on,
    COALESCE(other_pp.name, '') AS other_pricelist,
    ppi.price_discount AS price_discount,
    ppi.price_round AS price_rounding,
    ppi.price_max_margin AS max_price_margin,
    ppi.price_min_margin AS min_price_margin,
    ppi.price_surcharge AS extra_fee,
    ppi.price_surcharge AS fixed_price
FROM product_pricelist pp
LEFT JOIN product_pricelist_version ppv ON ppv.pricelist_id = pp.id
LEFT JOIN product_pricelist_item ppi ON ppi.price_version_id = ppv.id
LEFT JOIN product_category pc ON pc.id = ppi.categ_id
LEFT JOIN product_category pc2 ON pc2.id = pc.parent_id
LEFT JOIN product_category pc3 ON pc3.id = pc2.parent_id
LEFT JOIN product_product pp_v ON pp_v.id = ppi.product_id
left join product_attribute_value_product_product_rel pavppr on pavppr.prod_id = pp_v.id
left join product_attribute_value pav on pav.id = pavppr.att_id 
LEFT JOIN product_template pt ON pt.id = pp_v.product_tmpl_id
LEFT JOIN product_pricelist other_pp ON other_pp.id = ppi.base_pricelist_id
LEFT JOIN product_template pt_direct ON pt_direct.id = ppi.product_tmpl_id
WHERE ppi.base IN (1, -1)
and ppv.id in (
	-- Distinct Pricelist Version ID
	select
		distinct(ppv.id)
	FROM product_pricelist_version ppv
	LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
	where pp.id in (
		SELECT DISTINCT id
		FROM (
		    SELECT
		        pp.id
		    FROM product_pricelist pp
		    INNER JOIN wtc_branch wb 
		        ON wb.pricelist_unit_sales_id = pp.id or (wb.pricelist_unit_sales_id isnull and pp.name ilike '%%unit%%')
	        	OR wb.pricelist_unit_purchase_id = pp.id or (wb.pricelist_unit_purchase_id isnull and pp.name ilike '%%unit%%')
		    WHERE pp.active = true
		) AS subquery
	)
	and ppv.date_end >= '2026-05-06'
)
ORDER BY pp.name, ppv.name
limit 1

-- Pricelist Item BBN
select
	'tw_product_pricelist_item_' || lower(ppv.name) || '_' || lower(coalesce(
		CASE
		    WHEN ppi.categ_id IS NOT NULL THEN
		        concat_ws('_', pt.name, pav.code)
		    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
		        concat_ws('_', pt.name, pav.code)
		    ELSE
		        concat_ws('_', ppi.name::TEXT, pav.code)
		end, '')
	) as external_id,
    CASE
        WHEN ppi.categ_id IS NOT NULL THEN 'Category'
        ELSE 'Product'
    END AS display_applied_on,
    COALESCE(pc3.name || ' / ', '') ||
    COALESCE(pc2.name || ' / ', '') ||
    COALESCE(pc.name, '') AS category,
    CASE
	    WHEN ppi.categ_id IS NOT NULL THEN
	        concat_ws('|', pt.name, pav.code)
	    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
	        concat_ws('|', pt.name, pav.code)
	    ELSE
	        concat_ws('|', ppi.name::TEXT, pav.code)
	END as product_var_code,
	CASE
	    WHEN ppi.categ_id IS NOT NULL THEN
	        pt.name
	    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
	        pt.name
	    ELSE
	        ppi.name
	END as product,
	pav.code as attribute_code,
	pav.name as attribute_name,
    CASE
        WHEN pp_v.id IS NOT NULL THEN
            COALESCE(pt_direct.name, '')
        ELSE ''
    END AS variant,
    CASE
        WHEN ppi.base = -1 THEN 'Formula'
        WHEN ppi.base = 1 THEN 'Fixed Price'
        ELSE ''
    END AS compute_price,
    ppi.min_quantity AS min_quantity,
    ppv.name AS pricelist_version,
    pp.name AS pricelist,
    ppv.date_start AS start_date,
    ppv.date_end AS end_date,
    CASE
        WHEN ppi.base = 1 THEN 'Sales Price'
        WHEN ppi.base = -1 THEN 'Other Pricelist'
        ELSE ''
    END AS based_on,
    COALESCE(other_pp.name, '') AS other_pricelist,
    ppi.price_discount AS price_discount,
    ppi.price_round AS price_rounding,
    ppi.price_max_margin AS max_price_margin,
    ppi.price_min_margin AS min_price_margin,
    ppi.price_surcharge AS extra_fee,
    ppi.price_surcharge AS fixed_price
FROM product_pricelist pp
LEFT JOIN product_pricelist_version ppv ON ppv.pricelist_id = pp.id
LEFT JOIN product_pricelist_item ppi ON ppi.price_version_id = ppv.id
LEFT JOIN product_category pc ON pc.id = ppi.categ_id
LEFT JOIN product_category pc2 ON pc2.id = pc.parent_id
LEFT JOIN product_category pc3 ON pc3.id = pc2.parent_id
LEFT JOIN product_product pp_v ON pp_v.id = ppi.product_id
left join product_attribute_value_product_product_rel pavppr on pavppr.prod_id = pp_v.id
left join product_attribute_value pav on pav.id = pavppr.att_id 
LEFT JOIN product_template pt ON pt.id = pp_v.product_tmpl_id
LEFT JOIN product_pricelist other_pp ON other_pp.id = ppi.base_pricelist_id
LEFT JOIN product_template pt_direct ON pt_direct.id = ppi.product_tmpl_id
WHERE ppi.base IN (1, -1)
and ppv.id in (
	-- Distinct Pricelist Version ID
	select
		distinct(ppv.id)
	FROM product_pricelist_version ppv
	LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
	where pp.id in (
		SELECT DISTINCT id
		FROM (
		    SELECT
		        pp.id
		    FROM product_pricelist pp
		    INNER JOIN wtc_branch wb 
		        ON wb.pricelist_bbn_hitam_id = pp.id or (wb.pricelist_bbn_hitam_id isnull and pp.name ilike '%%bbn%%')
		        OR wb.pricelist_bbn_merah_id = pp.id or (wb.pricelist_bbn_merah_id isnull and pp.name ilike '%%bbn%%')
		    WHERE pp.active = true
		) AS subquery
	)
	and ppv.date_end >= '2026-05-18'
)
ORDER BY pp.name, ppv.name


--Pricelist Item BBN Beli Unit
select
	'tw_product_pricelist_item_' || lower(ppv.name) || '_' || lower(coalesce(
		concat_ws('_', pt.name, pav.code), '')
	) as external_id,
    '' AS category,
    concat_ws('|', pt.name, pav.code) as product_var_code,
	pt.name as product,
	pav.code as attribute_code,
	pav.name as attribute_name,
    CASE
        WHEN pp_v.id IS NOT NULL THEN
            COALESCE(pt.name, '')
        ELSE ''
    END AS variant,
    'Fixed Price' AS compute_price,
    '0' AS min_quantity,
    ppv.name AS pricelist_version,
    pp.name AS pricelist,
    ppv.start_date AS start_date,
    ppv.end_date AS end_date,
    'Sales Price' AS based_on,
    '' AS other_pricelist,
    '' AS price_discount,
    ppi.price_round AS price_rounding,
    ppi.price_max_margin AS max_price_margin,
    ppi.price_min_margin AS min_price_margin,
    ppi.price_surcharge AS extra_fee,
    ppi.price_surcharge AS fixed_price
FROM wtc_harga_bbn pp
LEFT JOIN wtc_harga_bbn_line ppv ON ppv.bbn_id = pp.id
LEFT JOIN wtc_harga_bbn_line_detail ppi ON ppi.harga_bbn_line_id = ppv.id
LEFT JOIN product_product pp_v ON pp_v.product_tmpl_id = ppi.product_template_id
left join product_template pt on pt.id = ppi.product_template_id 
left join product_attribute_value_product_product_rel pavppr on pavppr.prod_id = pp_v.id
left join product_attribute_value pav on pav.id = pavppr.att_id 
WHERE 
ppv.end_date >= '2026-05-18'
ORDER BY pp.name, ppv.name


--Pricelist Item BBN
SELECT
    'Product' AS display_applied_on,
    pt.name AS product,
    'Fixed Price' AS compute_price,
	whbl.name AS pricelist_version,
	REPLACE(whb.name, ',', ' ') AS pricelist,
    whbl.start_date,
    whbl.end_date,
    whbld.total AS fixed_price,
    wc.code AS city,
    whbld.notice AS notice_price,
    whbld.proses AS process_price,
    whbld.jasa AS serv_service,
    whbld.jasa_area AS serv_area_service,
    whbld.fee_pusat AS capital_fee_price
FROM wtc_harga_bbn whb
LEFT JOIN wtc_harga_bbn_line whbl ON whbl.bbn_id = whb.id and whbl.active = True
LEFT JOIN wtc_harga_bbn_line_detail whbld ON whbld.harga_bbn_line_id = whbl.id
LEFT JOIN wtc_city wc ON whbld.city_id = wc.id
LEFT JOIN product_template pt ON whbld.product_template_id = pt.id
where whbl.end_date >= '2026-05-18'

-- Pricelist Item Sparepart
select
	'tw_product_pricelist_item_' || lower(ppv.name) || '_' || lower(coalesce(
		CASE
		    WHEN ppi.categ_id IS NOT NULL THEN
		        concat_ws('_', pt.name, pav.code)
		    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
		        concat_ws('_', pt.name, pav.code)
		    ELSE
		        concat_ws('_', ppi.name::TEXT, pav.code)
		end, '')
	) as external_id,
    CASE
        WHEN ppi.categ_id IS NOT NULL THEN 'Category'
        ELSE 'Product'
    END AS display_applied_on,
    COALESCE(pc3.name || ' / ', '') ||
    COALESCE(pc2.name || ' / ', '') ||
    COALESCE(pc.name, '') AS category,
    CASE
	    WHEN ppi.categ_id IS NOT NULL THEN
	        concat_ws('|', pt.name, pav.code)
	    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
	        concat_ws('|', pt.name, pav.code)
	    ELSE
	        concat_ws('|', ppi.name::TEXT, pav.code)
	END as product_var_code,
	CASE
	    WHEN ppi.categ_id IS NOT NULL THEN
	        pt.name
	    WHEN length(ppi.name) > 5 AND length(pt.name) <= 5 THEN
	        pt.name
	    ELSE
	        ppi.name
	END as product,
	pav.code as attribute_code,
	pav.name as attribute_name,
    CASE
        WHEN pp_v.id IS NOT NULL THEN
            COALESCE(pt_direct.name, '')
        ELSE ''
    END AS variant,
    CASE
        WHEN ppi.base = -1 THEN 'Formula'
        WHEN ppi.base = 1 THEN 'Fixed Price'
        ELSE ''
    END AS compute_price,
    ppi.min_quantity AS min_quantity,
    ppv.name AS pricelist_version,
    pp.name AS pricelist,
    ppv.date_start AS start_date,
    ppv.date_end AS end_date,
    CASE
        WHEN ppi.base = 1 THEN 'Sales Price'
        WHEN ppi.base = -1 THEN 'Other Pricelist'
        ELSE ''
    END AS based_on,
    COALESCE(other_pp.name, '') AS other_pricelist,
    ppi.price_discount AS price_discount,
    ppi.price_round AS price_rounding,
    ppi.price_max_margin AS max_price_margin,
    ppi.price_min_margin AS min_price_margin,
    ppi.price_surcharge AS extra_fee,
    ppi.price_surcharge AS fixed_price
FROM product_pricelist pp
LEFT JOIN product_pricelist_version ppv ON ppv.pricelist_id = pp.id
LEFT JOIN product_pricelist_item ppi ON ppi.price_version_id = ppv.id
LEFT JOIN product_category pc ON pc.id = ppi.categ_id
LEFT JOIN product_category pc2 ON pc2.id = pc.parent_id
LEFT JOIN product_category pc3 ON pc3.id = pc2.parent_id
LEFT JOIN product_product pp_v ON pp_v.id = ppi.product_id
left join product_attribute_value_product_product_rel pavppr on pavppr.prod_id = pp_v.id
left join product_attribute_value pav on pav.id = pavppr.att_id 
LEFT JOIN product_template pt ON pt.id = pp_v.product_tmpl_id
LEFT JOIN product_pricelist other_pp ON other_pp.id = ppi.base_pricelist_id
LEFT JOIN product_template pt_direct ON pt_direct.id = ppi.product_tmpl_id
WHERE ppi.base IN (1, -1)
and ppv.id in (
	-- Distinct Pricelist Version ID
	select
		distinct(ppv.id)
	FROM product_pricelist_version ppv
	LEFT JOIN product_pricelist pp ON pp.id = ppv.pricelist_id
	where pp.id in (
		SELECT DISTINCT id
		FROM (
		    SELECT
		        pp.id
		    FROM product_pricelist pp
		    INNER JOIN wtc_branch wb 
		        ON wb.pricelist_part_purchase_id = pp.id or (wb.pricelist_part_purchase_id isnull and pp.name ilike '%%part%%')
		        OR wb.pricelist_part_sales_id = pp.id or (wb.pricelist_part_sales_id isnull and pp.name ilike '%%part%%')
		    WHERE pp.active = true
		) AS subquery
	)
	and ppv.date_end >= '2026-05-18'
)
ORDER BY pp.name, ppv.name