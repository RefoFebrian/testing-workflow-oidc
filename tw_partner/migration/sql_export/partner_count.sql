-- =============================================================================
-- Query untuk menghitung jumlah partner unik yang DIPERTAHANKAN
-- Gunakan hasilnya untuk menentukan pembagian batch di partner_export.sql
-- =============================================================================
WITH FilteredPartners AS (
    SELECT rp.*
    FROM res_partner rp
    WHERE rp.id > 6 
    AND default_code IN ('STK/23/09/13811','STK/23/06/19178','STK/20/02/11482','STK/15/07/16739','MML1760','STK/20/01/18078','STK/19/04/16802','U0005','STK/19/08/23563','STK/19/10/23999','STK/17/09/08899','SUMO')
),
RawCount AS (
    SELECT
        rp.id AS raw_id,
        rp.is_company,
        rp.default_code,
        COUNT(*) OVER (PARTITION BY NULLIF(TRIM(rp.default_code), '')) AS code_count,
        REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') AS digits_mobile,
        REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g') AS digits_ktp,
        REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g') AS digits_npwp,
        REGEXP_REPLACE(REGEXP_REPLACE(LOWER(TRIM(rp.name)), '^(pt\.|pt\s+|cv\.|cv\s+)', '', 'g'), '[^a-z0-9]', '', 'g') AS norm_name,
        COALESCE(REGEXP_REPLACE(TRIM(rp.name), E'[\\r\\n\\t]+', ' ', 'g'), '') AS "name",
        COALESCE(REGEXP_REPLACE(TRIM(rp.default_code), E'[\\r\\n\\t]+', ' ', 'g'), '') AS "code",
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g') ~ '(\d)\1{6,}' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g')) IN (15, 16) 
            THEN REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g')
            ELSE '' 
        END AS "clean_npwp",
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g') ~ '(\d)\1{6,}' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g')) = 16 
            THEN REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g')
            ELSE '' 
        END AS "clean_ktp",
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') ~ '(\d)\1{6,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') ~ '^080|^6280' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g')) < 10 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '08%' 
            THEN '+628' || SUBSTRING(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') FROM 3)
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '628%'
            THEN '+628' || SUBSTRING(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') FROM 4)
            WHEN NULLIF(TRIM(rp.mobile), '') LIKE '+628%'
            THEN NULLIF(TRIM(rp.mobile), '')
            ELSE '' 
        END AS "mobile_std",
        COALESCE(TRIM(rp.email), '') AS "email",
        COALESCE(TRIM(rp.street), '') AS "street"
    FROM FilteredPartners rp
),
PreRanked AS (
    SELECT 
        *,
        CASE 
            WHEN code_count > 1 AND NULLIF(TRIM("code"), '') IS NOT NULL AND TRIM("code") !~ '^(0|-|\.)$' THEN 'CODE_' || LOWER(TRIM("code"))
            WHEN (is_company OR LOWER("name") ~* '\y(pt|cv|ud|toko|pd|koperasi|yayasan|group|tbk|firma|perum|agency|asuransi|finance|cv\.|pt\.)\y') AND norm_name != '' 
            THEN 'COMPANY_' || norm_name
            WHEN LENGTH(clean_npwp) >= 15 AND clean_npwp !~ '^(.)+$' THEN 'NPWP_' || clean_npwp
            WHEN LENGTH(clean_ktp) = 16 AND clean_ktp !~ '^(.)+$' THEN 'KTP_' || clean_ktp
            WHEN mobile_std != '' THEN 'MOBILE_' || mobile_std
            WHEN norm_name != '' AND default_code LIKE '%-%' THEN 'NAME_' || norm_name || '_' || LOWER(TRIM(default_code))
            WHEN norm_name != '' THEN 'NAME_' || norm_name
            ELSE 'ID_' || CAST(raw_id AS VARCHAR) 
        END AS alasan_gabung
    FROM RawCount
),
Ranked AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY alasan_gabung
            ORDER BY 
                CASE WHEN "name" IS NULL OR TRIM("name") = '' OR TRIM("name") ~ '^[^a-zA-Z0-9]+$' THEN 0 ELSE 1 END DESC,
                CASE WHEN LENGTH(TRIM("code")) = 3 THEN 2 WHEN NULLIF(TRIM("code"), '') IS NOT NULL THEN 1 ELSE 0 END DESC,
                raw_id DESC 
        ) as rn
    FROM PreRanked
)
SELECT 
    COUNT(*) AS total_partner_dipertahankan,
    (SELECT COUNT(*) FROM Ranked) AS total_semua_termasuk_eliminasi,
    (SELECT COUNT(*) FROM Ranked WHERE rn > 1 OR "name" IS NULL OR TRIM("name") = '' OR TRIM("name") ~ '^[^a-zA-Z0-9]+$') AS total_dieliminasi
FROM Ranked
WHERE rn = 1 
  AND "name" IS NOT NULL 
  AND TRIM("name") != '' 
  AND TRIM("name") !~ '^[^a-zA-Z0-9]+$';
