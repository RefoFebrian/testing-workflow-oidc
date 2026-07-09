select
'tw_qr_code_unit_' || qr.name::varchar as "external_id",
qr.name as "name",
lot.name as "lot_id",
qr.qr_code_base64 as "qr_code_base64",
qr.date as "date",
he.nip  as "printed_uid",
qr.printed_date  as "printed_date",
qr.state as "state"
from teds_qr_code_unit qr
left join stock_production_lot lot on lot.id = qr.lot_id
left join res_users ru on ru.id = qr.printed_uid
left join resource_resource rr on rr.user_id = ru.id
left join hr_employee he on he.resource_id = rr.id