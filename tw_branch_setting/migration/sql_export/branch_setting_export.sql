-- BRANCH SETTING EXPORT SCRIPT FOR ODOO 18 EXCEL IMPORT
-- This script returns branch configurations in a one-to-many row format recognized by Odoo's Excel/CSV import.
-- Copy the results of this query, save them to Excel, and import them directly into the "tw.branch.setting" model.

WITH base_data AS (
  SELECT
    'tw_branch_' || LOWER(wb.code) AS ext_id,
    wb.name AS branch,
    'Account Setting ALL' AS account_setting,
    '' AS name,
    CASE WHEN whb.default_birojasa THEN 'TRUE' ELSE 'FALSE' END AS default_birojasa,
    CASE rp.default_code
      WHEN 'STK/22/06/01385' THEN 'MEGA'
      WHEN 'STK/22/06/01388' THEN 'MEGA'
      WHEN 'MEGA' THEN 'MEGA'
      WHEN 'OTO' THEN 'SOF'
      WHEN 'DWK1598' THEN 'HHO2725'
      WHEN 'STK/15/06/01453' THEN 'STK/18/04/10186'
      WHEN 'STK/15/06/01461' THEN 'HHO2724'
      WHEN 'DDJ7733' THEN 'MJB'
      WHEN 'DWG7389' THEN 'MJB'
      WHEN 'DWO4440' THEN 'MJB'
      WHEN 'DWM4439' THEN 'MJB'
      WHEN 'DWS4427' THEN 'MJB'
      WHEN 'DWR4431' THEN 'MJB'
      WHEN 'DXS2093' THEN 'MJB'
      WHEN 'DXK6780' THEN 'MJB'
      WHEN 'DWP4426' THEN 'MJB'
      WHEN 'DDA7777' THEN 'DDD7777'
      WHEN 'DDS7777' THEN 'DDD7777'
      WHEN 'STK/15/06/01445' THEN 'HHO2726'
      ELSE rp.default_code
    END AS biro_jasa,
    string_agg(DISTINCT REPLACE(whbbn.name, ',', ' '), ',') AS pricelists,
    he_pimpinan.nip AS branch_head,
    he_manager.nip AS area_manager,
    he_gm.nip AS general_manager,
    he_adh.nip AS admin_head,
    he_admin.nip AS admin_pos,
    he_kasir.nip AS cashier,
    'TRUE' AS po_need_approval,
    MIN(rp_exp.default_code) AS default_expedition,
    wa.description AS default_area,
    wba1.name AS area_1,
    wba2.name AS area_2,
    regexp_replace(wb.npwp, '[^0-9]', '', 'g') AS npwp,
    regexp_replace(wb.no_pkp, '[^0-9]', '', 'g') AS pkp,
    wb.professional_allowance_params AS professional_allowance,
    wb.city_wage_rate AS umr,
    wb.state_wage_rate AS ump,
    'TRUE' AS calculate_incentive,
    whb.id AS birojasa_record_id,
    regexp_replace(loc_rpa_add.complete_name, '^[^/]+/', '') AS location_rpa_additional,
    regexp_replace(loc_rpa_top.complete_name, '^[^/]+/', '') AS location_rpa_topup,
    regexp_replace(loc_rpa_hot.complete_name, '^[^/]+/', '') AS location_rpa_hotline,
    regexp_replace(loc_rpa_back.complete_name, '^[^/]+/', '') AS location_rpa_backup_hotline,
    wb.plafon_petty_cash_sr,
    wb.plafon_petty_cash_ws,
    wb.plafon_petty_cash_atl_btl,
    pp_up.name AS pricelist_unit_purchase_id,
    pp_pp.name AS pricelist_part_purchase_id,
    pp_us.name AS pricelist_unit_sales_id,
    pp_bh.name AS pricelist_bbn_hitam_id,
    pp_bm.name AS pricelist_bbn_merah_id,
    pp_ps.name AS pricelist_part_sales_id,
    aa_ica.code AS inter_company_account_id,
    wb.blind_bonus_beli,
    wb.blind_bonus_jual,
    wb.blind_bonus_beli_performance
  FROM wtc_branch wb
  LEFT JOIN wtc_harga_birojasa whb ON whb.branch_id=wb.id
  LEFT JOIN res_partner rp ON whb.birojasa_id=rp.id
  LEFT JOIN wtc_harga_bbn whbbn ON whb.harga_bbn_id=whbbn.id AND whbbn.active = TRUE
  LEFT JOIN hr_employee he_pimpinan ON wb.pimpinan_id=he_pimpinan.id
  LEFT JOIN resource_resource rr_pimpinan ON he_pimpinan.resource_id=rr_pimpinan.id
  LEFT JOIN hr_employee he_manager ON wb.manager_id=he_manager.id
  LEFT JOIN resource_resource rr_manager ON he_manager.resource_id=rr_manager.id
  LEFT JOIN hr_employee he_gm ON wb.general_manager_id=he_gm.id
  LEFT JOIN resource_resource rr_gm ON he_gm.resource_id=rr_gm.id
  LEFT JOIN hr_employee he_admin ON wb.admin_pos_id=he_admin.id
  LEFT JOIN resource_resource rr_admin ON he_admin.resource_id=rr_admin.id
  LEFT JOIN hr_employee he_adh ON wb.adh_id=he_adh.id
  LEFT JOIN resource_resource rr_adh ON he_adh.resource_id=rr_adh.id
  LEFT JOIN hr_employee he_kasir ON wb.kasir_id=he_kasir.id
  LEFT JOIN resource_resource rr_kasir ON he_kasir.resource_id=rr_kasir.id
  LEFT JOIN wtc_area wa ON wb.area_id=wa.id
  LEFT JOIN wtc_branch_area wba1 ON wb.branch_area_1=wba1.id
  LEFT JOIN wtc_branch_area wba2 ON wb.branch_area_2=wba2.id
  LEFT JOIN wtc_branch_config wbc ON wbc.branch_id = wb.id
  LEFT JOIN stock_location loc_rpa_add ON wbc.rpa_additional_location_id = loc_rpa_add.id
  LEFT JOIN stock_location loc_rpa_top ON wbc.rpa_topup_location_id = loc_rpa_top.id
  LEFT JOIN stock_location loc_rpa_hot ON wbc.rpa_hotline_location_id = loc_rpa_hot.id
  LEFT JOIN stock_location loc_rpa_back ON wbc.rpa_backup_hotline_location_id = loc_rpa_back.id
  LEFT JOIN product_pricelist pp_up ON wb.pricelist_unit_purchase_id = pp_up.id AND pp_up.active = TRUE
  LEFT JOIN product_pricelist pp_pp ON wb.pricelist_part_purchase_id = pp_pp.id AND pp_pp.active = TRUE
  LEFT JOIN product_pricelist pp_us ON wb.pricelist_unit_sales_id = pp_us.id AND pp_us.active = TRUE
  LEFT JOIN wtc_harga_bbn pp_bh ON wb.pricelist_bbn_hitam_id = pp_bh.id AND pp_bh.active = TRUE
  LEFT JOIN wtc_harga_bbn pp_bm ON wb.pricelist_bbn_merah_id = pp_bm.id AND pp_bm.active = TRUE
  LEFT JOIN product_pricelist pp_ps ON wb.pricelist_part_sales_id = pp_ps.id AND pp_ps.active = TRUE
  LEFT JOIN account_account aa_ica ON wb.inter_company_account_id = aa_ica.id
  LEFT JOIN wtc_harga_ekspedisi whe ON whe.branch_id = wb.id AND whe.default_ekspedisi = TRUE
  LEFT JOIN res_partner rp_exp ON whe.ekspedisi_id = rp_exp.id
  GROUP BY wb.code, wb.name, whb.id, whb.default_birojasa, 
    CASE rp.default_code
      WHEN 'STK/22/06/01385' THEN 'MEGA'
      WHEN 'STK/22/06/01388' THEN 'MEGA'
      WHEN 'MEGA' THEN 'MEGA'
      WHEN 'OTO' THEN 'SOF'
      WHEN 'DWK1598' THEN 'HHO2725'
      WHEN 'STK/15/06/01453' THEN 'STK/18/04/10186'
      WHEN 'STK/15/06/01461' THEN 'HHO2724'
      WHEN 'DDJ7733' THEN 'MJB'
      WHEN 'DWG7389' THEN 'MJB'
      WHEN 'DWO4440' THEN 'MJB'
      WHEN 'DWM4439' THEN 'MJB'
      WHEN 'DWS4427' THEN 'MJB'
      WHEN 'DWR4431' THEN 'MJB'
      WHEN 'DXS2093' THEN 'MJB'
      WHEN 'DXK6780' THEN 'MJB'
      WHEN 'DWP4426' THEN 'MJB'
      WHEN 'DDA7777' THEN 'DDD7777'
      WHEN 'DDS7777' THEN 'DDD7777'
      WHEN 'STK/15/06/01445' THEN 'HHO2726'
      ELSE rp.default_code
    END, 
    he_pimpinan.nip, he_manager.nip,
           he_gm.nip, he_admin.nip, he_kasir.nip, wa.description, wba1.name, wba2.name,
           wb.npwp, wb.no_pkp, wb.city_wage_rate, wb.state_wage_rate, loc_rpa_add.complete_name,
           loc_rpa_top.complete_name, loc_rpa_hot.complete_name, loc_rpa_back.complete_name, wb.plafon_petty_cash_sr, wb.plafon_petty_cash_ws,
           wb.plafon_petty_cash_atl_btl, pp_up.name, pp_pp.name, pp_us.name, pp_bh.name, pp_bm.name, pp_ps.name, aa_ica.code, aa_ica.name,
           wb.blind_bonus_beli, wb.blind_bonus_beli_performance, wb.blind_bonus_jual, he_adh.nip, wb.professional_allowance_params
),
numbered_data AS (
  SELECT *,
    branch AS branch_sort,
    ROW_NUMBER() OVER (PARTITION BY branch ORDER BY
      CASE WHEN default_birojasa = 'TRUE' THEN 0 ELSE 1 END,
      biro_jasa NULLS LAST
    ) AS rn
  FROM base_data
)
SELECT
  CASE WHEN rn = 1 THEN ext_id ELSE '' END AS "External ID",
  CASE WHEN rn = 1 THEN branch ELSE '' END AS "Branch",
  CASE WHEN rn = 1 THEN account_setting ELSE '' END AS "Account Setting",
  CASE WHEN rn = 1 THEN name ELSE '' END AS "Name",
  
  -- One2many Relation Fields (Birojasa Settings)
  default_birojasa AS "Birojasa Settings/Default",
  COALESCE(biro_jasa, '') AS "Birojasa Settings/Biro Jasa/default_code",
  COALESCE(pricelists, '') AS "Birojasa Settings/Pricelists",
  
  -- Parent Fields
  CASE WHEN rn = 1 THEN branch_head ELSE '' END AS "Branch Head/nik",
  CASE WHEN rn = 1 THEN area_manager ELSE '' END AS "Area Manager/nik",
  CASE WHEN rn = 1 THEN general_manager ELSE '' END AS "General Manager/nik",
  CASE WHEN rn = 1 THEN admin_head ELSE '' END AS "Admin Head/nik",
  CASE WHEN rn = 1 THEN admin_pos ELSE '' END AS "Admin POS/nik",
  CASE WHEN rn = 1 THEN cashier ELSE '' END AS "Cashier/nik",
  CASE WHEN rn = 1 THEN po_need_approval ELSE '' END AS "PO Need Approval",
  CASE WHEN rn = 1 THEN default_expedition ELSE '' END AS "Default Expedition/default_code",
  CASE WHEN rn = 1 THEN default_area ELSE '' END AS "Default Area",
  CASE WHEN rn = 1 THEN area_1 ELSE '' END AS "Area 1",
  CASE WHEN rn = 1 THEN area_2 ELSE '' END AS "Area 2",
  CASE WHEN rn = 1 THEN npwp ELSE '' END AS "NPWP",
  CASE WHEN rn = 1 THEN pkp ELSE '' END AS "PKP",
  CASE WHEN rn = 1 THEN professional_allowance ELSE NULL END AS "Tunjangan Profesi (%)",
  CASE WHEN rn = 1 THEN umr ELSE NULL END AS "UMR",
  CASE WHEN rn = 1 THEN ump ELSE NULL END AS "UMP",
  CASE WHEN rn = 1 THEN calculate_incentive ELSE '' END AS "Calculate Incentive on Confirm",
  CASE WHEN rn = 1 THEN location_rpa_additional ELSE '' END AS "Location RPA Additional",
  CASE WHEN rn = 1 THEN location_rpa_topup ELSE '' END AS "Location RPA Topup/Simpart",
  CASE WHEN rn = 1 THEN location_rpa_hotline ELSE '' END AS "Location RPA Hotline",
  CASE WHEN rn = 1 THEN location_rpa_backup_hotline ELSE '' END AS "Location RPA Backup Hotline",
  CASE WHEN rn = 1 THEN plafon_petty_cash_sr ELSE NULL END AS "Plafon Petty Cash SR",
  CASE WHEN rn = 1 THEN plafon_petty_cash_ws ELSE NULL END AS "Plafon Petty Cash WS",
  CASE WHEN rn = 1 THEN plafon_petty_cash_atl_btl ELSE NULL END AS "Plafon Petty Cash ATL/BTL",
  CASE WHEN rn = 1 THEN pricelist_unit_purchase_id ELSE '' END AS "Price List Beli Unit",
  CASE WHEN rn = 1 THEN pricelist_part_purchase_id ELSE '' END AS "Price List Beli Sparepart",
  CASE WHEN rn = 1 THEN pricelist_unit_sales_id ELSE '' END AS "Price List Jual Unit",
  CASE WHEN rn = 1 THEN pricelist_bbn_hitam_id ELSE '' END AS "Pricelist Sale BBN Hitam",
  CASE WHEN rn = 1 THEN pricelist_bbn_merah_id ELSE '' END AS "Pricelist Sale BBN Merah",
  CASE WHEN rn = 1 THEN pricelist_part_sales_id ELSE '' END AS "Price List Jual Sparepart",
  CASE WHEN rn = 1 THEN inter_company_account_id ELSE '' END AS "Account Intercompany/Code",
  CASE WHEN rn = 1 THEN blind_bonus_beli ELSE NULL END AS "Purchase Blind Bonus Amount",
  CASE WHEN rn = 1 THEN blind_bonus_jual ELSE NULL END AS "Sale Blind Bonus Amount",
  CASE WHEN rn = 1 THEN blind_bonus_beli_performance ELSE NULL END AS "Purchase Performance Blind Bonus Amount",
  
  -- Inherited Fields Placeholders
  CASE WHEN rn = 1 THEN '' ELSE '' END AS "Pricelist Sale BBN Putih",
  CASE WHEN rn = 1 THEN '' ELSE '' END AS "Pricelist Service",
  CASE WHEN rn = 1 THEN 'FALSE' ELSE '' END AS "DGI Auto Confirm PO",
  CASE WHEN rn = 1 THEN 'FALSE' ELSE '' END AS "CDB Data Mandatory (DGI DSO)?",
  CASE WHEN rn = 1 THEN 'FALSE' ELSE '' END AS "Allow Cancel SO with Payment",
  CASE WHEN rn = 1 THEN 'TRUE' ELSE '' END AS "Need Approval JM Cancel",
  CASE WHEN rn = 1 THEN '' ELSE '' END AS "Official WA Config",
  CASE WHEN rn = 1 THEN '' ELSE '' END AS "Unofficial WA Config",
  CASE WHEN rn = 1 THEN '' ELSE '' END AS "DGI Config",
  CASE WHEN rn = 1 THEN 0.0 ELSE NULL END AS "Minimal DP Part Hotline (%)"
FROM numbered_data
ORDER BY branch_sort, rn;