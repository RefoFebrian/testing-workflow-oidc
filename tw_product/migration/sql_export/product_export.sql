
WITH base_products AS (
    SELECT
        pt.id AS product_tmpl_id,
        '__import__.tw_product_template_' ||
            regexp_replace(lower(pt.name), '[^a-z0-9]+', '_', 'g') AS ext_id,
        pt.name,
        pt.description,
        pt.kd_mesin AS kode_mesin,
        wps.name AS product_series,
        pc3.name || ' / ' || pc2.name || ' / ' || pc.name AS internal_category,
        'PricelistServiceCategory|' || sc.name AS service_category
    FROM product_template pt
    LEFT JOIN wtc_product_series wps
        ON pt.series_id = wps.id
    LEFT JOIN product_category pc
        ON pt.categ_id = pc.id
    LEFT JOIN product_category pc2
        ON pc.parent_id = pc2.id
    LEFT JOIN product_category pc3
        ON pc2.parent_id = pc3.id
    LEFT JOIN wtc_category_product sc
        ON sc.id = pt.category_product_id
    WHERE pc3.name = 'Unit'
      AND pt.active IS TRUE
),
attribute_lines AS (
    SELECT
        ptal.product_tmpl_id,
        ptal.id AS ptal_id,
        pa.name AS attribute_name,
        string_agg(
            pav.code,
            ',' ORDER BY pav.sequence, pav.id
        ) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS attribute_value_codes,

        string_agg(
            regexp_replace(trim(pav.name), '\s+', ' ', 'g'),
            ',' ORDER BY pav.sequence, pav.id
        ) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS attribute_value_names,
        string_agg(
            upper(trim(pav.code)) || '|' || upper(regexp_replace(trim(pav.name), '\s+', ' ', 'g')),
            ' || ' ORDER BY pav.sequence, pav.id
        ) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS attribute_value_mapping_keys,
        min(pav.sequence) FILTER (
            WHERE pav.code IS NOT NULL
              AND pav.code <> '00'
        ) AS first_value_sequence
    FROM product_attribute_line ptal
    JOIN product_attribute pa
        ON pa.id = ptal.attribute_id
    LEFT JOIN product_attribute_line_product_attribute_value_rel rel
        ON rel.line_id = ptal.id
    LEFT JOIN product_attribute_value pav
        ON pav.id = rel.val_id
    GROUP BY
        ptal.product_tmpl_id,
        ptal.id,
        pa.name
),
prepared AS (
    SELECT
        bp.*,
        al.attribute_name,
        al.attribute_value_codes,
        al.attribute_value_names,
        al.attribute_value_mapping_keys,
        row_number() OVER (
            PARTITION BY bp.product_tmpl_id
            ORDER BY coalesce(al.first_value_sequence, 999999), al.ptal_id
        ) AS rn
    FROM base_products bp
    LEFT JOIN attribute_lines al
        ON al.product_tmpl_id = bp.product_tmpl_id
)
SELECT
    CASE WHEN rn = 1 THEN ext_id ELSE '' END AS id,
    CASE WHEN rn = 1 THEN name ELSE '' END AS name,
    CASE WHEN rn = 1 THEN description ELSE '' END AS description,
    CASE WHEN rn = 1 THEN kode_mesin ELSE '' END AS "Kode Mesin",
    CASE WHEN rn = 1 THEN product_series ELSE '' END AS "Product Series",
    CASE WHEN rn = 1 THEN internal_category ELSE '' END AS "Internal Category",
    CASE WHEN rn = 1 THEN service_category ELSE '' END AS "Service Category",
    CASE WHEN rn = 1 THEN 'Unit' ELSE '' END AS division,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS sale_ok,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS purchase_ok,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS is_storable,
    CASE WHEN rn = 1 THEN 'True' ELSE '' END AS lot_valuated,
    CASE WHEN rn = 1 THEN 'By Unique Serial Number' ELSE '' END AS tracking,
    CASE WHEN rn = 1 THEN 'Goods' ELSE '' END AS type,
    COALESCE(attribute_name, '') AS "attribute_line_ids/attribute_id",
    COALESCE(attribute_value_codes, '') AS "attribute_line_ids/value_ids",
    COALESCE(attribute_value_names, '') AS "TEDS Attribute Value Names",
    COALESCE(attribute_value_mapping_keys, '') AS "TEDS Mapping Keys"
FROM prepared
ORDER BY product_tmpl_id, rn;