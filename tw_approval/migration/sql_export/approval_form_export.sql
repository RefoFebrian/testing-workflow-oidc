select  form || ' - ' || code as name ,* from ( 
select 
case
	when wac.code = ' ' and wac.kategori is null then 'other' 
	when wac.kategori = 'rutin' then 'recurring'
	when wac.kategori = 'tidak_rutin' then 'non_recurring'
	when im.name = 'wtc.subsidi.barang' then ''
	else coalesce(wac.code,'other') 
end as code,
case
	when im.name = 'wtc.program.subsidi' then 'Master Sales Program'
	when im.name = 'Petty Cash' then 'Petty Cash Out'
	when im.name = 'Work Order' then 'tw.work.order'
	when im.name = 'Tagihan Biro Jasa' then 'Tagihan Birojasa'
	when im.name = 'Reimbursed Petty Cash' then 'Reimbursement Petty Cash'
	when im.name = 'MD Sales Order Cancel' then 'Sale Order Cancel'		
	when im.name = 'Disbursment EDC Cancel' then 'Disbursement Cancel'
	when im.name = 'Collecting AR/AP Cancel' then 'Collecting Cancel'
	when im.name = 'wtc.cancel.pajak.progressive' then 'tw.progressive.tax'
	when im.name = 'Change Lot' then 'Permohonan Perubahan Data'	
	when im.name = 'Account Voucher Custom' and wac.code ='purchase' then 'Account Payment'
	when im.name = 'Account Voucher Custom' and wac.code ='receipt' then 'Account Payment'
	when im.name = 'Account Voucher Custom' and wac.code ='payment' then 'Account Payment'
	when im.name = 'Account Voucher Custom' and wac.code = ' ' then 'Account Payment'
	when im.name = 'Debit and Credit Note Custom' and wac.code ='purchase' then 'Payment Request'
	when im.name = 'Debit and Credit Note Custom' and wac.code ='sale' then 'Other Receivable'	
	when im.name = 'teds.part.hotline' then 'TW Part Hotline'	
	when im.name = 'teds.part.hotline.cancel' then 'Part Hotline Cancel'
	when im.name = 'teds.mutation.request.asset' then 'Asset Mutation' 
	when im.name = 'teds.mutation.asset' then 'Asset Distribution'
	when im.name = 'teds.stock.opname.asset' then 'TW Stock Opname Asset'
	when im.name = 'settlement' then 'tw.settlement'
	when im.name = 'Dealer Sales Order Cancel' then 'Dealer Sale Order Cancel'
	when im.name = 'Birojasa Cancel' then 'Tagihan Birojasa Cancel'
	when im.name = 'purchase Order Cancel' then 'Purchase Order Cancel'
	when im.name = 'Purchase Asset' then 'Purchase Order Asset'
	when im.name = 'Return Pembelian' then 'Purchase Return'
	when im.name = 'Unit Bundling' then 'Manufacturing Order'
	when im.name = 'Checklist Tool Bengkel' then 'Checklist Tool'
	when im.name = 'Proposal Perjalanan Dinas' then 'Business Trip / Perjalanan Dinas'
	else im.name
end as form,
wac.type,
write_uid.name as write_uid,
TO_CHAR(wac.write_date  , 'YYYY-MM-DD HH24:MI:SS') as write_date
from wtc_approval_config wac
	inner join ir_model im on im.id = wac.form_id  
	left join res_users write_usr on write_usr.id = wac.write_uid    
	left join res_partner write_uid on write_uid.id = write_usr.partner_id
where im.name not in ('Return Penjualan','Picking List','Purchase Requisition','Accounting Voucher','Request Platform','Surat Penawaran','Internal Memo Online','Request Payment','Account Type','wtc.subsidi.barang','Master Program Voucher')
) as approval