select
'tw_vehicle_ownership_location_' || lower(wb.code) || '_' || lower(replace(bpkb.name,' ','_')) as "External ID",
bpkb.name as "Location Name",
wb.code as "Branch",
bpkb.description,
bpkb.alamat as "Address",
wc.code as "City",
bpkb.type as "Location Type"
from wtc_lokasi_bpkb bpkb
left join wtc_branch wb on wb.id = bpkb.branch_id
left join wtc_city wc on wc.id = bpkb.city_id