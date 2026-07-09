SELECT
	rb.name AS bank,
	rpb.acc_number AS account_number,
	rpb.owner_name AS account_holder_name,
	rpb.bank_bic AS code,
	rp.name AS account_holder,
	'' AS qris_api_key,
	'' AS qris_merchant_id,
	CASE
	    WHEN COALESCE(rpba.flag_check_account, FALSE) THEN 'TRUE'
	    ELSE 'FALSE'
	END AS cek_nama_ke_popeye,
	'' AS is_match_check_account,
	'TRUE' AS allow_send_money,
	'TRUE' AS active
FROM res_partner_bank rpb
LEFT JOIN res_bank rb ON rpb.bank = rb.id
LEFT JOIN res_partner rp ON rpb.partner_id = rp.id
LEFT JOIN res_partner_bank_account rpba ON (
	rpb.partner_id = rpba.partner_id
	AND rpb.bank = rpba.bank_id
	AND rpb.acc_number = rpba.account_number
)
WHERE rpb.owner_name IS NOT NULL
  AND TRIM(rpb.owner_name) <> ''
  AND rpb.acc_number IS NOT NULL
  AND TRIM(rpb.acc_number) <> '';