-- ACCOUNT SETTING EXPORT SCRIPT FOR ODOO 18 EXCEL IMPORT
-- This script returns a single global configuration record formatted for standard Odoo 18 import.
-- Copy the results of this query, save them to Excel, and import them directly into the "tw.account.setting" model.

SELECT
    'tw_account_setting.account_setting_all' AS "External ID",
    'Account Setting ALL' AS "Description",
    wbc.nilai_pembulatan AS "Nilai Pembulatan",
    aa.code AS "Account Pembulatan/Code",
    aa2.code AS "Account PL Disbursement/Code",
    aj.name AS "Journal Pembatalan Disbursement EDC/Name",
    aa3.code AS "Bank Transfer Fee Account/Code",
    aj2.name AS "Journal Payment Request/Name",
    aj3.name AS "Journal Payment Cancel/Name",
    aj4.name AS "Journal Settlement/Name",
    aj5.name AS "Journal Memorial/Name",
    aj6.name AS "Journal Collecting AR/AP/Name",
    aj7.name AS "Journal Other Receivable/Name",
    aj8.name AS "Journal Advance Payment/Name",
    aa4.code AS "Account Collecting Sisa Voucher/Code",
    aj9.name AS "Journal Collecting Voucher/Name",
    aa5.code AS "Account Blind Bonus Unit Purchase Dr/Code",
    aa6.code AS "Account Blind Bonus Unit Purchase Cr/Code",
    aa7.code AS "Account Blind Bonus Unit Purchase Performance Dr/Code",
    aa8.code AS "Account Blind Bonus Unit Purchase Performance Cr/Code",
    aj10.name AS "Journal Blind Bonus Unit Purchase/Name",
    aj11.name AS "Journal Purchase Unit/Name",
    aj12.name AS "Journal Purchase Sparepart/Name",
    aj13.name AS "Journal Purchase Umum/Name",
    aa9.code AS "Account Discount Cash Supplier/Code",
    aj14.name AS "Journal Purchase Unit Cancel/Name",
    aj15.name AS "Journal Sales Unit/Name",
    aj16.name AS "Journal Sales Sparepart/Name",
    aj17.name AS "Journal Blind Bonus Unit Sales/Name",
    aj18.name AS "Journal WO Regular/Name",
    aj19.name AS "Journal Accrue Tax/Name",
    aj24.name AS "Journal Collecting Piutang Claim/Name",
    aj25.name AS "Journal Work Order Cancel/Name",
    aj26.name AS "Journal Pelunasan SO/Name",
    aj27.name AS "Journal Hutang Komisi/Name",
    aj28.name AS "Journal Incentive Finco/Name",
    aa10.code AS "Account Sisa Program Subsidi/Code",
    aj29.name AS "Journal Voucher/Name",
    aj30.name AS "Journal Extra Reward/Name",
    aj31.name AS "Journal Dealer Sale Order Cancel/Name",
    aa11.code AS "Account Sales BBN/Code",
    aj32.name AS "Journal Purchase BBN/Name",
    aj33.name AS "Journal BBN Beli/Name",
    aj34.name AS "Journal Pajak Progressive/Name",
    aj35.name AS "Journal Birojasa Billing Cancel/Name",
    aa12.code AS "Account Gain/Loss/Code",
    aa13.code AS "Account Expense Asset/Code",
    aj36.name AS "Journal Disposal Asset/Name",
    aj37.name AS "Journal Hutang Lain Reconcile/Name",
    aj38.name AS "Journal Asset Adjustment/Name",
    aj39.name AS "Journal Purchase Return/Name",
    aj18.name AS "Journal Part Sales Umum/Name",
    aj18.name AS "Journal Part Sales Sparepart/Name",
    aj25.name AS "Journal Part Sales Cancel/Name",
    aj27.name AS "Journal Hutang Komisi WO/Name",
    aj40.name AS "Journal Downpayment/Name",
    aj41.name AS "Journal Alokasi DP/Name",
    aa14.code AS "Account Discount Regular/Code",
    aa15.code AS "Account Discount Quotation/Code",
    aj42.name AS "Journal Subsidi Finco/Name",
    aj43.name AS "Journal Subsidi MD/Name",
    wb.accrue_ekspedisi AS "Amount Accure Expedition",
    aj44.name AS "Journal Accrue Dana Ongkos Angkut/Name",
    CASE
        WHEN wb.accrue_ekspedisi IS NOT NULL OR COALESCE(aj44.name, '') <> '' THEN 'TRUE'
        ELSE 'FALSE'
    END AS "Accrue Expedition?",
    aj45.name AS "Journal Direct Gift MD/Name",
    aj46.name AS "Journal Direct Gift Finco/Name",
    CASE WHEN wb.is_accrue_proses_bbn_active THEN 'TRUE' ELSE 'FALSE' END AS "Accrue Proses BBN?",
    aj44.name AS "Journal Ekspedisi/Name",
    aj47.name AS "Journal BBN Jual/Name"
FROM wtc_branch_config wbc
LEFT JOIN wtc_branch wb ON wbc.branch_id = wb.id
LEFT JOIN account_account aa ON wbc.wtc_account_voucher_pembulatan_account_id = aa.id
LEFT JOIN account_account aa2 ON wbc.disburesement_pl_account_id = aa2.id
LEFT JOIN account_account aa3 ON wbc.bank_transfer_fee_account_id = aa3.id
LEFT JOIN account_account aa4 ON wbc.account_collecting_sisa_voucher_id = aa4.id
LEFT JOIN account_account aa5 ON wbc.wtc_po_account_blind_bonus_beli_dr_id = aa5.id
LEFT JOIN account_account aa6 ON wbc.wtc_po_account_blind_bonus_beli_cr_id = aa6.id
LEFT JOIN account_account aa7 ON wbc.wtc_po_account_blind_bonus_performance_dr_id = aa7.id
LEFT JOIN account_account aa8 ON wbc.wtc_po_account_blind_bonus_performance_cr_id = aa8.id
LEFT JOIN account_account aa9 ON wbc.wtc_po_account_discount_cash_id = aa9.id
LEFT JOIN account_account aa10 ON wbc.dealer_so_account_sisa_subsidi_id = aa10.id
LEFT JOIN account_account aa11 ON wbc.dealer_so_account_bbn_jual_id = aa11.id
LEFT JOIN account_account aa12 ON wbc.gain_loss_account_id = aa12.id
LEFT JOIN account_account aa13 ON wbc.expense_asset_account_id = aa13.id
LEFT JOIN account_account aa14 ON wbc.dealer_so_account_potongan_langsung_id = aa14.id
LEFT JOIN account_account aa15 ON wbc.dealer_so_account_potongan_subsidi_id = aa15.id
LEFT JOIN account_journal aj ON wbc.disbursement_cancel_journal_id = aj.id
LEFT JOIN account_journal aj2 ON wbc.wtc_payment_request_account_id = aj2.id
LEFT JOIN account_journal aj3 ON wbc.payment_cancel_journal_id = aj3.id
LEFT JOIN account_journal aj4 ON wbc.settlement_journal_id = aj4.id
LEFT JOIN account_journal aj5 ON wbc.journal_memorial_journal_id = aj5.id
LEFT JOIN account_journal aj6 ON wbc.journal_collecting_id = aj6.id
LEFT JOIN account_journal aj7 ON wbc.wtc_other_receivable_account_id = aj7.id
LEFT JOIN account_journal aj8 ON wbc.avp_journal_id = aj8.id
LEFT JOIN account_journal aj9 ON wbc.journal_collecting_voucher_id = aj9.id
LEFT JOIN account_journal aj10 ON wbc.wtc_po_journal_blind_bonus_beli_id = aj10.id
LEFT JOIN account_journal aj11 ON wbc.wtc_po_journal_unit_id = aj11.id
LEFT JOIN account_journal aj12 ON wbc.wtc_po_journal_sparepart_id = aj12.id
LEFT JOIN account_journal aj13 ON wbc.wtc_po_journal_umum_id = aj13.id
LEFT JOIN account_journal aj14 ON wbc.purchase_order_cancel_journal_id = aj14.id
LEFT JOIN account_journal aj15 ON wbc.wtc_so_journal_unit_id = aj15.id
LEFT JOIN account_journal aj16 ON wbc.wtc_so_journal_sparepart_id = aj16.id
LEFT JOIN account_journal aj17 ON wbc.wtc_so_journal_bind_bonus_jual_id = aj17.id
LEFT JOIN account_journal aj18 ON wbc.wo_reg_journal_id = aj18.id
LEFT JOIN account_journal aj19 ON wbc.wo_accrue_tax_journal_id = aj19.id
LEFT JOIN account_journal aj20 ON wbc.wo_claim_lcr_journal_id = aj20.id
LEFT JOIN account_journal aj21 ON wbc.wo_kpb_journal_id = aj21.id
LEFT JOIN account_journal aj22 ON wbc.wo_collecting_kpb_journal_id = aj22.id
LEFT JOIN account_journal aj23 ON wbc.wo_claim_journal_id = aj23.id
LEFT JOIN account_journal aj24 ON wbc.wo_collecting_claim_journal_id = aj24.id
LEFT JOIN account_journal aj25 ON wbc.work_order_cancel_journal_id = aj25.id
LEFT JOIN account_journal aj26 ON wbc.dealer_so_journal_pelunasan_id = aj26.id
LEFT JOIN account_journal aj27 ON wbc.dealer_so_journal_hc_id = aj27.id
LEFT JOIN account_journal aj28 ON wbc.dealer_so_journal_insentive_finco_id = aj28.id
LEFT JOIN account_journal aj29 ON wbc.dealer_so_journal_voucher_id = aj29.id
LEFT JOIN account_journal aj30 ON wbc.dealer_so_journal_extra_reward_id = aj30.id
LEFT JOIN account_journal aj31 ON wbc.dso_cancel_journal_id = aj31.id
LEFT JOIN account_journal aj32 ON wbc.dealer_so_journal_bbnbeli_id = aj32.id
LEFT JOIN account_journal aj33 ON wbc.tagihan_birojasa_bbn_journal_id = aj33.id
LEFT JOIN account_journal aj34 ON wbc.tagihan_birojasa_progressive_journal_id = aj34.id
LEFT JOIN account_journal aj35 ON wbc.birojasa_cancel_journal_id = aj35.id
LEFT JOIN account_journal aj36 ON wbc.journal_disposal_asset_id = aj36.id
LEFT JOIN account_journal aj37 ON wbc.journal_disposal_asset_hl_id = aj37.id
LEFT JOIN account_journal aj38 ON wbc.journal_asset_adjustment_id = aj38.id
LEFT JOIN account_journal aj39 ON wbc.wtc_retur_pembelian_journal_unit_id = aj39.id
LEFT JOIN account_journal aj40 ON wbc.dealer_so_journal_dp_id = aj40.id
LEFT JOIN account_journal aj41 ON wbc.dealer_so_journal_hl_id = aj41.id
LEFT JOIN account_journal aj42 ON wbc.dealer_so_journal_psfinco_id = aj42.id
LEFT JOIN account_journal aj43 ON wbc.dealer_so_journal_psmd_id = aj43.id
LEFT JOIN account_journal aj44 ON wbc.freight_cost_journal_id = aj44.id
LEFT JOIN account_journal aj45 ON wbc.dealer_so_journal_bbmd_id = aj45.id
LEFT JOIN account_journal aj46 ON wbc.dealer_so_journal_bbfinco_id = aj46.id
LEFT JOIN account_journal aj47 ON wbc.offtr_to_ontr_bbn_jual_journal_id = aj47.id
LIMIT 1;