WITH base_data AS (
  SELECT
    'Harga Jasa - ' || wwc.name AS pricelist_name,
    'TRUE' AS active,
    'Sales' AS pricelist_type,
    whjv.name AS version_name,
    whjv.date_start AS start_date,
    whjv.date_end AS end_date,
    CASE
        WHEN whjv.active THEN 'Active'
        ELSE ''
    END AS state,
    'Product' AS display_applied_on,
    pt.name AS product,
    'Fixed Price' AS compute_price,
    wcp.name AS service_category,
    whj.price AS fixed_price,
    whj.id AS record_id
  FROM wtc_harga_jasa whj
  JOIN wtc_workshop_category wwc ON wwc.id = whj.workshop_category
  JOIN wtc_harga_jasa_version whjv ON whjv.id = whj.harga_jasa_version_id
  JOIN product_product pp ON pp.id = whj.product_id_jasa
  JOIN product_template pt ON pt.id = pp.product_tmpl_id
  JOIN wtc_category_product wcp ON wcp.id = whj.category_product_id
),
numbered_data AS (
  SELECT *,
    pricelist_name AS pricelist_sort,
    version_name AS version_sort,
    ROW_NUMBER() OVER (
      PARTITION BY pricelist_name, version_name
      ORDER BY record_id
    ) AS rn
  FROM base_data
)
SELECT
  CASE WHEN rn = 1 THEN pricelist_name ELSE '' END AS pricelist_name,
  CASE WHEN rn = 1 THEN active ELSE '' END AS active,
  CASE WHEN rn = 1 THEN pricelist_type ELSE '' END AS pricelist_type,
  CASE WHEN rn = 1 THEN version_name ELSE '' END AS version_name,
  CASE WHEN rn = 1 THEN start_date ELSE NULL END AS start_date,
  CASE WHEN rn = 1 THEN end_date ELSE NULL END AS end_date,
  CASE WHEN rn = 1 THEN state ELSE '' END AS state,
  display_applied_on,
  product,
  compute_price,
  start_date,
  end_date,
  service_category,
  fixed_price
FROM numbered_data
ORDER BY pricelist_sort, version_sort, rn;