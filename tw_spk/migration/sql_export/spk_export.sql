select wb.code  as branch,
partner_id.default_code as customer,
partner_id.name as sales_person,
ds.state as status,
tsp.name as activity_type,
spal.name as activity_plan_id,
cancel_uid.name as cancel_uid,
TO_CHAR(ds.cancel_date  , 'YYYY-MM-DD HH24:MI:SS') as cancel_date,
confirm_uid.name as confirm_uid,
TO_CHAR(ds.confirm_date  , 'YYYY-MM-DD HH24:MI:SS') as confirm_date,
ds.alamat_kirim as delivery_address,
ds.division,
case 
	when finco.id is not null and finco.name LIKE 'PT %' then replace(finco.name,'PT','PT.')
	else finco.name
end as finco_id,
case 
	when ds.jaringan_penjualan = 'Chanel/Mediator'
	then 'SalesChannel|channel'
	else 'SalesChannel|' || LOWER(ds.jaringan_penjualan)
end as sales_channel,
ds.reason_cancel,
'' as sales_source_location,
case
	when dsl.is_bbn = 'Y' then true 
	else false
end as line_ids_is_bbn,
case
	when product.id is not null then product.name_template|| '|' ||pav.code
end as line_ids_product_id,
dsl.product_qty as line_ids_product_qty,
coalesce(tl.uang_muka,dsl.uang_muka)as line_ids_down_payment,
dsl.discount_po as line_ids_discount,
partner_stnk.default_code as line_ids_partner_stnk_id,
dsl.plat as line_ids_plate_id,
case 
	when tl.payment_type = '1' then 'Cash'
	else 'Credit'
end as tipe_pembayaran 
from dealer_spk ds
inner join wtc_branch wb on ds.branch_id = wb.id
inner join res_partner partner_id on partner_id.id = ds.partner_id 
inner join hr_employee he on he.id = ds.user_id 
left join teds_act_type_sumber_penjualan tsp on ds.sumber_penjualan_id = tsp.id
left join teds_sales_plan_activity_line spal on spal.id = ds.activity_plan_id
left join res_users cancel_usr on cancel_usr.id = ds.cancel_uid 
left join res_partner cancel_uid on cancel_uid.id = cancel_usr.partner_id 
left join res_users confirm_usr on confirm_usr.id = ds.confirm_uid  
left join res_partner confirm_uid on confirm_uid.id = confirm_usr.partner_id 
left join res_users create_usr on create_usr.id = ds.create_uid   
left join res_partner create_uid on create_uid.id = create_usr.partner_id 
left join res_partner finco on finco.id = ds.finco_id
left join res_users write_usr on write_usr.id = ds.write_uid    
left join res_partner write_uid on write_uid.id = write_usr.partner_id
left join res_partner partner on partner.id = ds.partner_id 
left join stock_location sl on sl.id = ds.sales_source_location 
left join dealer_spk_line dsl on dsl.dealer_spk_line_id = ds.id
left join product_product product on product.id = dsl.product_id 
left join product_attribute_value_product_product_rel pavpp on pavpp.prod_id = product.id
left join product_attribute_value pav on pavpp.att_id = pav.id
left join res_partner partner_stnk on partner_stnk.id = dsl.partner_stnk_id 
left join teds_lead tl on tl.spk_id = ds.id
order by ds.id desc