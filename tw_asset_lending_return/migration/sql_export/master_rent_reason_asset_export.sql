-- MIGRATION REASON PEMINJAMAN ASET
SELECT 
	'tw_master_rent_reason_asset_' || id AS "External ID",
	name AS "Alasan Peminjaman Asset"
FROM teds_master_peminjaman_asset_reason