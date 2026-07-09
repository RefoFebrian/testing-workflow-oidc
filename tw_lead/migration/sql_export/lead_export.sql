select 
tl.name,
tl.no_refrence as reference,
tl.name_customer as Customer_Name,
CASE
    WHEN tl.mobile IS NULL THEN NULL
    ELSE
        CASE
            WHEN clean ~ '^0?8[0-9]{8,11}$'
                THEN '+62' || SUBSTRING(clean FROM '^0?(8[0-9]+)$')
            WHEN clean ~ '^62?8[0-9]{8,11}$'
                THEN '+62' || SUBSTRING(clean FROM '^62?(8[0-9]+)$')
            ELSE NULL
        END
END AS mobile,
hr.nip as sales_id,
TO_CHAR(tl.create_date, 'YYYY-MM-DD HH24:MI:SS') as create_date,
tsp.name as activity_type,
spal.name as activity_plan_id,
wq.name as agama,
tl.cicilan as angsuran,
b.code as branch,
tl.is_btl as btl,
tl.name_customer as contact_name,
rp.name as create_uid,
'IDR' as currency,
partner_id.default_code as customer,
cust_stnk_id.default_code as customer_stnk,
tl.data_source as data_source,
''''|| TO_CHAR(tl.date, 'YYYY-MM-DD') as date,
deal_by.name as dealt_by,
TO_CHAR(tl.deal_date, 'YYYY-MM-DD HH24:MI:SS')::Text as dealt_on,
tl.diskon,
tl.email,
tl.email as email_from,
tl.email as email_cc,
tl.email as email_domain_criterion,
tl.facebook,
case 
	when finco.id is not null and finco.name LIKE 'PT %' then replace(finco.name,'PT','PT.')
	else finco.name
end as finco_id,
case 
	when gol_darah.name is not null then 'BloodType|' || gol_darah.value
	else gol_darah.name 
end as golongan_darah,
hobi.name as hobby,
tl.no_kk as identification_family_number,
tl.no_ktp as identification_number,
tl.instagram,
INITCAP(tl.minat) as minat,
jenis_kelamin.name as jenis_kelamin,
c.code as kabupaten,
c_domisile.code as kabupaten_domisili,
kec.code as kecamatan,
kec_domisili.code as kecamatan_domisili,
zip.code as kelurahan,
zip_domisili.code as kelurahan_domisili,
case 
	when tl.atas_nama_stnk is not null and tl.atas_nama_stnk = 'sendiri' then 'MotorOwnership|self'
	when tl.atas_nama_stnk is not null and tl.atas_nama_stnk = 'orang_lain' then 'MotorOwnership|other'
	else tl.atas_nama_stnk
end as kepemilikan_motor,
case 
	when kepemilikan_rumah.name is not null and kepemilikan_rumah.name = 'Rumah Orang Tua/Keluarga' then 'Rumah Orang Tua'
	else kepemilikan_rumah.name 
end as kepemilikan_rumah,
case 
	when tla.id is not null then tl.name || ' - ' || tls.name
	else null
end as lead_activity,
tl.motor_sekarang,
case 
	when tl.atas_nama_stnk = 'sendiri' then 'self'
	else 'other'
end as motor_ownership,
'Indonesia' as negara,
'Indonesia' as negara_domisili,
case 
	when tla.id is not null then tl.name || ' - ' || next_tls.name
	else null
end as next_activity,
tl.follow_ke as follow_up_count,
tl.note,
tl.otr,
rc.name as parent_company,
case 
	when tl.payment_type = '1' then 'Cash'
	else 'Credit'
end as payment_type,
case
	when pekerjaan.name is not null then 'Occupation|' || pekerjaan.value
	else pekerjaan.name
end as pekerjaan,
pendidikan.name as pendidikan,
case
	when pengeluaran.value is not null then 'Expense|' || pengeluaran.value
	else pengeluaran.name 
end as pengeluaran,
case 
	when pengguna.name is not null then 'MotorUser|' || pengguna.value
	else pengguna.name
end as pengguna_motor,
case 
	when penggunaan.name is not null then 'MotorUtilization|' || penggunaan.value
	else penggunaan.name
end as penggunaan_motor,
case
	when product.id is not null then product.name_template|| '|' ||pav.code
end as product,
prov.code as provinsi,
prov_domisili.code as provinsi_domisili,
tla.remark as lead_activity_remark,
tla.minat as lead_activity_interest,
result_activity.name as lead_activity_result,
TO_CHAR(tla.date , 'YYYY-MM-DD HH24:MI:SS') as lead_activity_done_date,
tl.rt,
tl.rt_domisili,
tl.rw,
tl.rw_domisili,
case 
	when tl.jaringan_penjualan = 'Chanel/Mediator'
	then 'SalesChannel|channel'
	else 'SalesChannel|' || LOWER(tl.jaringan_penjualan)
end as sales_channel,
CASE
    WHEN tl.mobile IS NULL THEN NULL
    ELSE
        CASE
            WHEN clean ~ '^0?8[0-9]{8,11}$'
                THEN '+62' || SUBSTRING(clean FROM '^0?(8[0-9]+)$')
            WHEN clean ~ '^62?8[0-9]{8,11}$'
                THEN '+62' || SUBSTRING(clean FROM '^62?(8[0-9]+)$')
            ELSE NULL
        END
END AS sanitized_number,
tl.is_sesuai_ktp as is_same_ktp,
CASE 
    WHEN tls.name IS NULL THEN NULL
    WHEN tls.name = 'MESSAGE' THEN 'SMS'
    ELSE INITCAP(tls.name)
end as lead_activity_stage,
case 
	when tl.state is not null and tl.state = 'dealt' then 'spk'
	else tl.state
end as state,
case
	when status_paket_data.name = 'Prabayar / Isi Ulang' then 'Prabayar'
	when status_paket_data.name = 'Pasca-bayar / Billing / Tagihan' then 'Pascabayar'
end as status_paket_data,
tl.street,
tl.street_domisili,
tl.date_jatuh_tempo as tanggal_jatuh_tempo,
tl.tempat_tgl_lahir as tempat_lahir,
''''|| TO_CHAR(tl.tgl_lahir, 'YYYY-MM-DD') as tanggal_lahir,
''''|| TO_CHAR(tl.tgl_uang_muka, 'YYYY-MM-DD') as down_payment_date,
tl.tenor,
case 
	when tl.payment_type = '1' then 'Cash'
	else 'Credit'
end as tipe_pembayaran,
titik_keramaian.name as titik_keramaian,
tl.twitter,
'Lead' as type,
tl.uang_muka,
b.name as user_company,
tl.version_code,
tl.version_name,
tl.youtube,
zip.zip,
zip_domisili.zip as zip_domisili
FROM (
    select
        tl.*,
        REGEXP_REPLACE(tl.mobile, '[^0-9]', '', 'g') AS clean
    FROM teds_lead tl
) tl
inner join hr_employee hr on hr.id = tl.employee_id
left join teds_act_type_sumber_penjualan tsp on tl.sumber_penjualan_id = tsp.id
left join teds_sales_plan_activity_line spal on spal.id = tl.activity_plan_id
left join teds_sales_plan_activity spa on spa.id = spal.activity_id
left join wtc_questionnaire wq on wq.id = tl.agama_id
inner join wtc_branch b on b.id = tl.branch_id
left join wtc_city c on c.id = tl.kabupaten_id 
left join res_users usr on usr.id = tl.create_uid
left join res_partner rp on rp.id = usr.partner_id
left join res_partner partner_id on partner_id.id = tl.customer_id
left join res_partner cust_stnk_id on cust_stnk_id.id = tl.customer_stnk_id
left join res_users usr_deal_by on usr_deal_by.id = tl.deal_uid
left join res_partner deal_by on deal_by.id = usr_deal_by.partner_id
left join res_partner finco on finco.id = tl.finco_id
left join wtc_questionnaire gol_darah on gol_darah.id = tl.gol_darah
left join wtc_questionnaire hobi on hobi.id = tl.hobi
left join wtc_questionnaire jenis_kelamin on jenis_kelamin.id = tl.jenis_kelamin_id
left join wtc_city c_domisile on c_domisile.id = tl.kabupaten_domisili_id 
left join wtc_kecamatan kec on kec.id = tl.kecamatan_id
left join wtc_kecamatan kec_domisili on kec_domisili.id = tl.kecamatan_domisili_id
left join wtc_questionnaire kepemilikan_rumah on kepemilikan_rumah.id = tl.status_rumah_id
left join teds_lead_activity tla on tla.lead_id = tl.id
left join teds_lead_stage tls on tls.id = tla.name
left join teds_lead_activity next_tla on next_tla.id = tl.next_activity_id
left join teds_lead_stage next_tls on next_tls.id = next_tla.name
left join teds_master_result_lead_activity result_activity on result_activity.id = tla.stage_result_id
left join res_company rc on rc.id = b.company_id
left join wtc_questionnaire pekerjaan on pekerjaan.id = tl.pekerjaan_id
left join wtc_questionnaire pendidikan on pendidikan.id = tl.pendidikan_id
left join wtc_questionnaire pengeluaran on pengeluaran.id = tl.pengeluaran_id
left join wtc_questionnaire pengguna on pengguna.id = tl.pengguna_id
left join wtc_questionnaire penggunaan on penggunaan.id = tl.penggunaan_id
left join product_product product on product.id = tl.product_id
left join product_template pt on pt.id = product.product_tmpl_id
left join product_attribute_value_product_product_rel pavpp on pavpp.prod_id = product.id
left join product_attribute_value pav on pavpp.att_id = pav.id
left join res_country_state prov on prov.id = tl.state_id
left join res_country_state prov_domisili on prov_domisili.id = tl.state_id
left join hr_employee sales_coordinator on sales_coordinator.id = tl.sales_koordinator_id
left join hr_employee sales_person on sales_person.id = tl.employee_id
left join wtc_questionnaire status_paket_data on status_paket_data.id = tl.status_hp_id
left join titik_keramaian titik_keramaian on titik_keramaian.id = tl.titik_keramaian_id
left join wtc_kelurahan zip on zip.id = tl.zip_code_id
left join wtc_kelurahan zip_domisili on zip_domisili.id = tl.zip_code_domisili_id
order by tl.id desc