select
'tw_api_master_partner_bundling_' || lower(rb.code) as "Bunding/External ID",
'tw_api_master_partner_bundling_line_' || lower(SUBSTRING(rp.display_name FROM '\[(.*?)\]')) as "Bundling Line/External ID",
rb.code as branch_code,
SUBSTRING(rp.display_name FROM '\[(.*?)\]') AS partner_code,
'res_partner_' || lower(SUBSTRING(rp.display_name FROM '\[(.*?)\]')) as "Partner/External ID"
from teds_api_master_partner_bundling_line tpbl
left join teds_api_master_partner_bundling tpb on tpb.id = tpbl.branch_bundling_id
left join res_partner rp on rp.id = tpbl.partner_id
left join wtc_branch rb on rb.id = tpb.branch_id
order by tpb.branch_id asc