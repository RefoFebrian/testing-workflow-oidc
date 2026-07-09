-- Migration Query: Export legacy API Configurations from TEDS 1.0 (Odoo 8/9) to TEDS 2.0 (Odoo 18)
-- Targets Odoo 18 model: tw.api.configuration
-- To be executed on legacy database (TEDS 1.0) and imported via Odoo 18 Import Tool
--
-- Column mapping resolves:
-- - Relational company mapped by res.company code ("company_id/code")
-- - Relational tw.selection mapped by type/value code pattern ("api_type_id")

WITH ConfigAPINormal AS (
    SELECT 
        'teds_api_configuration' AS source_model,
        CASE 
            WHEN tac.username = 'admin_api' THEN 'HoKI'
            ELSE 'API CONFIG - ' || COALESCE(tac.username, '') 
        END AS name,
        CASE 
            WHEN tac.username = 'admin_api' THEN 'https://hoki.honda-ku.com'
            ELSE COALESCE(tac.host, '') || CASE WHEN tac.port IS NOT NULL AND tac.port <> '' THEN ':' || tac.port ELSE '' END 
        END AS base_url,
        tac.username AS username,
        tac.password AS password,
        'basic' AS auth_type,
        COALESCE(wb.code, '') AS company_code,
        CASE 
            WHEN tac.username = 'admin_api' THEN 'ApiType|Hoki'
            ELSE 'ApiType|Umum'
        END AS api_type_id,
        '' AS api_key,
        '' AS api_secret,
        '' AS token,
        '' AS client_id,
        '' AS client_secret,
        '' AS code,
        ROW_NUMBER() OVER (
            PARTITION BY wb.code, CASE WHEN tac.username = 'admin_api' THEN 'HoKI' ELSE tac.username END 
            ORDER BY tac.id DESC
        ) AS rn
    FROM teds_api_configuration tac
    LEFT JOIN wtc_branch wb ON wb.id = tac.branch_id
    WHERE tac.is_config_wa IS NOT TRUE
),

ConfigWATokens AS (
    SELECT 
        'teds_api_configuration_token' AS source_model,
        'API WA-Blast ' || COALESCE(wb.code, '') AS name,
        COALESCE(tact.url, '') AS base_url,
        COALESCE(tac.username, '') AS username,
        COALESCE(tac.password, '') AS password,
        'basic' AS auth_type,
        COALESCE(wb.code, '') AS company_code,
        'ApiType|Whatsapp' AS api_type_id,
        '' AS api_key,
        '' AS api_secret,
        COALESCE(tact.token, '') AS token,
        '' AS client_id,
        '' AS client_secret,
        '' AS code,
        ROW_NUMBER() OVER (
            PARTITION BY wb.code 
            ORDER BY tact.id DESC
        ) AS rn
    FROM teds_api_configuration tac
    INNER JOIN teds_api_configuration_token tact ON tact.config_id = tac.id
    LEFT JOIN wtc_branch wb ON wb.id = tac.branch_id
    WHERE tac.is_config_wa IS TRUE AND wb.code IS NOT NULL AND wb.code <> ''
),

ConfigB2B AS (
    SELECT 
        'teds_b2b_api_config' AS source_model,
        COALESCE(tbac.name, '') AS name,
        COALESCE(tbac.base_url, '') AS base_url,
        COALESCE(tbac.username, '') AS username,
        COALESCE(tbac.password, '') AS password,
        'basic' AS auth_type,
        '' AS company_code,
        CASE 
            WHEN tbac.name ILIKE '%popeye%' OR tbac.code::text = 'popeye' THEN 'ApiType|popeye'
            WHEN tbac.name ILIKE '%peruri%' OR tbac.name ILIKE '%emeterai%' THEN 'ApiType|peruri_emeterai'
            WHEN tbac.name ILIKE '%telegram%' THEN 'ApiType|Telegram'
            WHEN tbac.name ILIKE '%koprol%' OR tbac.code::text = 'koprol' THEN 'ApiType|koprol_2'
            ELSE 'ApiType|Umum'
        END AS api_type_id,
        COALESCE(tbac.api_key, '') AS api_key,
        COALESCE(tbac.api_secret, '') AS api_secret,
        '' AS token,
        COALESCE(tbac.client_id, '') AS client_id,
        COALESCE(tbac.client_secret, '') AS client_secret,
        COALESCE(tbac.code::text, '') AS code,
        ROW_NUMBER() OVER (
            PARTITION BY tbac.name, tbac.code::text 
            ORDER BY tbac.id DESC
        ) AS rn
    FROM teds_b2b_api_config tbac
    WHERE tbac.is_dgi IS NOT TRUE
      AND tbac.name NOT ILIKE '%dgi%'
      AND tbac.code::text NOT ILIKE '%dgi%'
),

CombinedConfig AS (
    SELECT * FROM ConfigAPINormal WHERE rn = 1
    UNION ALL
    SELECT * FROM ConfigWATokens WHERE rn = 1
    UNION ALL
    SELECT * FROM ConfigB2B WHERE rn = 1
)

SELECT 
    name AS "name",
    base_url AS "base_url",
    username AS "username",
    password AS "password",
    api_key AS "api_key",
    api_secret AS "api_secret",
    token AS "token",
    client_id AS "client_id",
    client_secret AS "client_secret",
    code AS "code",
    auth_type AS "auth_type",
    company_code AS "company_id/code",
    api_type_id AS "api_type_id"
FROM CombinedConfig
ORDER BY "api_type_id", "company_id/code", "name";
