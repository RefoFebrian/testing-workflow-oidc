select
'tw_kpb_expired_' || lower(replace(name,' ','_')) || '_' || lower(replace(description,' ','_')) || '_' || service as external_id,
name as engine_code,
description,
service,
hari,
km
from wtc_kpb_expired
order by engine_code