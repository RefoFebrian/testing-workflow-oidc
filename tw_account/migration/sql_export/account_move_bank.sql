WITH RawData AS (
    SELECT 
        wb.code AS branch,
        aa.code AS account_code,
        CASE 
            WHEN teds_reconciled_rk IS TRUE THEN 'Opening Balance' 
            ELSE am.name || ' - ' || aml.name || ' - ' || COALESCE(aml.REF, '') 
        END AS label,
        SUM(debit) - SUM(credit) AS net_amount
    FROM account_move_line aml
    JOIN account_move am ON am.id = aml.move_id 
    LEFT JOIN wtc_branch wb ON wb.id = aml.branch_id
    JOIN account_account aa ON aa.id = aml.account_id 
    JOIN account_account_type AS aat ON aat.id = aa.user_type
--    WHERE aa.code IN ('11122400MML', '11122900MML') 
    WHERE aa.type = 'liquidity'
    AND aat.name = 'Bank'
    GROUP BY 1, 2, 3
    HAVING (SUM(debit) - SUM(credit)) != 0 -- Only keep branches that have a balance
),
ProcessedLines AS (
    -- 1. DETAIL LINES
    SELECT branch, account_code, label,
           CASE WHEN net_amount > 0 THEN net_amount ELSE 0 END AS debit,
           CASE WHEN net_amount < 0 THEN ABS(net_amount) ELSE 0 END AS credit,
           1 AS line_priority, -- Forces detail to top
           account_code AS source_account
    FROM RawData
    UNION ALL
    -- 2. BALANCING LINES
    SELECT branch, 
           '899999' AS account_code, 
           'Offset for ' || account_code || ' [' || branch || ']',
           -- Reverse the math: if source is Debit, offset is Credit
           CASE WHEN SUM(net_amount) < 0 THEN ABS(SUM(net_amount)) ELSE 0 END AS debit,
           CASE WHEN SUM(net_amount) > 0 THEN SUM(net_amount) ELSE 0 END AS credit,
           9 AS line_priority, -- Forces balancing line to bottom
           account_code AS source_account
    FROM RawData
    GROUP BY branch, account_code
)
SELECT 
    -- Header logic: Reset count based on the branch and the original account
    CASE 
        WHEN ROW_NUMBER() OVER(PARTITION BY branch, source_account ORDER BY line_priority ASC) = 1 
        THEN 'IMP/' || source_account || '/' || branch 
        ELSE NULL 
    END AS "name",
    CASE WHEN ROW_NUMBER() OVER(PARTITION BY branch, source_account ORDER BY line_priority ASC) = 1 
         THEN 'Reconciled Opening Balance' ELSE NULL END AS "REF",
    CASE WHEN ROW_NUMBER() OVER(PARTITION BY branch, source_account ORDER BY line_priority ASC) = 1 
         THEN '2023-12-31' ELSE NULL END AS "date",
    CASE WHEN ROW_NUMBER() OVER(PARTITION BY branch, source_account ORDER BY line_priority ASC) = 1 
         THEN 'Miscellaneous' ELSE NULL END AS "journal_id",
    branch AS "line_ids/branch_id",
    account_code AS "line_ids/account_id",
    label AS "line_ids/name",
    debit AS "line_ids/debit",
    credit AS "line_ids/credit"
FROM ProcessedLines
ORDER BY branch ASC, source_account ASC, line_priority ASC;