-- Unit
SELECT
    '__import__.tw.p2p.product_' || wpp.id AS "External ID"
    , COALESCE(
    	'[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')',
    	'[' || pt.name || '] ' || pp.default_code
    ) AS "Product / Database ID"
    , COALESCE(
    	pt.name || '-' || pav.code,
    	CASE
	    	WHEN pt.name LIKE '0%' THEN '''' || pt.name
	    	ELSE pt.name
	  	END
    ) AS "Mapping Product"
    , CASE
    	WHEN wpp.division = 'Unit' THEN pt.name
    	ELSE pp.default_code
    END AS "Name"
    , wpp.start_date AS "Start Date"
    , wpp.end_date AS "End Date"
    , COALESCE(pc3.name || ' / ' || pc2.name || ' / ' || pc.name, pc2.name || ' / ' || pc.name) AS "Category"
    , pc.name AS "Sub Category"
    , CASE
    	WHEN wpp.division != 'Unit' THEN pc.name
    ELSE NULL END AS "Category Fix Order"
    , wpp.division AS "Division"
    , TRUE AS "Active"
FROM wtc_p2p_product wpp
LEFT JOIN product_product pp ON wpp.product_id = pp.id
LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
LEFT JOIN product_attribute_value_product_product_rel pavpp ON pavpp.prod_id = pp.id
LEFT JOIN product_attribute_value pav ON pavpp.att_id = pav.id
LEFT JOIN product_category pc ON pt.categ_id = pc.id
LEFT JOIN product_category pc2 ON pc.parent_id = pc2.id
LEFT JOIN product_category pc3 ON pc2.parent_id = pc3.id
WHERE 1=1
AND wpp.division = 'Unit'
AND wpp.product_id IS NOT NULL;

-- Sparepart
SELECT
    '__import__.tw.p2p.product_' || wpp.id AS "External ID"
    , COALESCE(
    	'[' || pt.name || '] ' || pt.description || ' (' || split_part(pav.name, '-', 2) || ')',
    	'[' || pt.name || '] ' || pp.default_code
    ) AS "Product / Database ID"
    , COALESCE(
    	pt.name || '-' || pav.code,
    	CASE
	    	WHEN pt.name LIKE '0%' THEN '''' || pt.name
	    	ELSE pt.name
	  	END
    ) AS "Mapping Product"
    , CASE
    	WHEN wpp.division = 'Unit' THEN pt.name
    	ELSE pp.default_code
    END AS "Name"
    , wpp.start_date AS "Start Date"
    , wpp.end_date AS "End Date"
    , COALESCE(pc3.name || ' / ' || pc2.name || ' / ' || pc.name, pc2.name || ' / ' || pc.name) AS "Category"
    , pc.name AS "Sub Category"
    , CASE
    	WHEN wpp.division != 'Unit' THEN pc.name
    ELSE NULL END AS "Category Fix Order"
    , wpp.division AS "Division"
    , TRUE AS "Active"
FROM wtc_p2p_product wpp
LEFT JOIN product_product pp ON wpp.product_id = pp.id
LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
LEFT JOIN product_attribute_value_product_product_rel pavpp ON pavpp.prod_id = pp.id
LEFT JOIN product_attribute_value pav ON pavpp.att_id = pav.id
LEFT JOIN product_category pc ON pt.categ_id = pc.id
LEFT JOIN product_category pc2 ON pc.parent_id = pc2.id
LEFT JOIN product_category pc3 ON pc2.parent_id = pc3.id
WHERE 1=1
AND wpp.division = 'Sparepart'
AND wpp.product_id IS NOT NULL;



-- Mapping Product ID on TETO (UNIT)
SELECT
    pt.default_code || '-' || pav.code AS product
   , pp.id
FROM product_template pt
LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id
LEFT JOIN product_category pc ON pt.categ_id = pc.id
LEFT JOIN product_category parent ON pc.parent_id = parent.id
LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
WHERE 1=1
AND (pt.division = 'Unit' OR parent.name = 'Unit');

-- Mapping Product ID on TETO (SPAREPART)
SELECT
    CASE
    	WHEN pt.default_code LIKE '0%' THEN '''' || pt.default_code
    	ELSE pt.default_code
  	END AS default_code
   , pp.id
FROM product_template pt
LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id
LEFT JOIN product_category pc ON pt.categ_id = pc.id
LEFT JOIN product_category parent ON pc.parent_id = parent.id
WHERE 1=1
AND (pt.division = 'Sparepart' OR parent.name = 'Sparepart');