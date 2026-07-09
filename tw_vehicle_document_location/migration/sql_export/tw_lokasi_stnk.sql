select
'tw_vehicle_registration_location_' || lower(wb.code) || '_' || lower(replace(stnk.name,' ','_')) as "External ID",
stnk.name as "Location Name",
wb.code as "Branch",
stnk.description,
stnk.alamat as "Address",
wc.code as "City",
stnk.type as "Location Type"
from wtc_lokasi_stnk stnk
left join wtc_branch wb on wb.id = stnk.branch_id
left join wtc_city wc on wc.id = stnk.city_id