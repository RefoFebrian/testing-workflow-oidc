WITH approval_unique AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY division, branch_id, form_id
               ORDER BY create_date DESC
           ) AS rn_hdr
    FROM wtc_approval_matrixbiaya_header
)
SELECT 
    CASE WHEN line_data.rn = 1 THEN wb.code ELSE '' END as branch,
    CASE WHEN line_data.rn = 1 THEN approval_biaya.division ELSE '' END as division,
    CASE WHEN line_data.rn = 1 THEN model.name || ' - ' || model.code  end as Form, 
    Upper(line_data.group_name) as "approval_lines/group_id",
    line_data.limit as "approval_lines/limit"
FROM approval_unique approval_biaya 
INNER JOIN wtc_branch wb ON wb.id = approval_biaya.branch_id 
INNER JOIN (
    SELECT 
        abl.header_id,
        abl.id as line_id,
        g.name as group_name,
        abl."limit",
        ROW_NUMBER() OVER (PARTITION BY abl.header_id ORDER BY abl.id) as rn
    FROM wtc_approval_matrixbiaya abl
    LEFT JOIN res_groups g ON g.id = abl.group_id
) AS line_data ON line_data.header_id = approval_biaya.id
LEFT JOIN res_users write_usr ON write_usr.id = approval_biaya.write_uid    
LEFT JOIN res_partner write_uid ON write_uid.id = write_usr.partner_id
left join (
select wac.id,
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
    else im.name end as name
    from ir_model as im
    left join wtc_approval_config wac on wac.form_id = im.id
) as model on approval_biaya.form_id = model.id
where model.name not in ('Return Penjualan','Picking List','Purchase Requisition','Accounting Voucher','Request Platform','Surat Penawaran','Internal Memo Online','Request Payment','Account Type','wtc.subsidi.barang','Master Program Voucher') and approval_biaya.rn_hdr = 1
ORDER by approval_biaya.id, line_data.rn