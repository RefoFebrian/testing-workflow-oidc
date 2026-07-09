# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date,timedelta
from math import e 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWDealerSaleOrderPenjualanReport(models.TransientModel):
    _name = "tw.dealer.sale.order.penjualan.report"
    _description = "Dealer Sale Order Penjualan Report"

    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    report_type = fields.Selection([
        ('',''),
        ('all','Penjualan'),
        ('salesman','Salesman'), 
        ('konsumen','Konsumen')], string='Report Type', default='all', help="Pilih tipe laporan penjualan : \nPenjualan: Laporan Penjualan\nSalesman: Laporan Penjualan Salesman\nKonsumen: Laporan Penjualan Konsumen\n\nTiap tipe laporan memerlukan access group tersendiri, apabila tidak punya access harap hubungi pihak Helpdesk")

    state_options = fields.Selection([
        ('all','All'), 
        ('sale','Outstanding'), 
        ('done','Paid'), 
        ('progress_done','Outstanding & Paid'), 
        ('progress_done_cancelled', 'Outstanding, Paid & Cancelled'), 
        ('cancel','Cancelled'),
    ], 'State Options', default='progress_done_cancelled')

    sales_id = fields.Many2one('hr.employee', string='Sales Person')
    sales_coordinator_id = fields.Many2one('hr.employee', string='Sales Coordinator')
    
    company_ids = fields.Many2many('res.company','tw_dso_penjualan_company_rel', 'report_id', 'company_id', string="Branch")
    product_ids = fields.Many2many('product.product', 'tw_dso_report_penjualan_product_rel', 'report_id', 'product_id', string='Product')
    finco_ids = fields.Many2many('res.partner', 'tw_dso_report_penjualan_finco_rel', 'report_id', 'finco_id', string='Finco')

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise Warning('Start Date must be less than End Date')

    @api.onchange('report_type')
    def onchange_report_type(self):
        if self.report_type == 'salesman':
            user_access = self.env.user.has_group('tw_dealer_sale_order.group_tw_dso_report_sales_salesman_read')
            if not user_access:
                raise Warning('You do not have access to this report type\n\nPlease contact your helpdesk for more information')
        elif self.report_type == 'konsumen':
            user_access = self.env.user.has_group('tw_dealer_sale_order.group_tw_dso_report_sales_konsumen_read')
            if not user_access:
                raise Warning('You do not have access to this report type\n\nPlease contact your helpdesk for more information')
        elif self.report_type == 'all':
            user_access = self.env.user.has_group('tw_dealer_sale_order.group_tw_dso_report_sales_all_read')
            if not user_access:
                raise Warning('You do not have access to this report type\n\nPlease contact your helpdesk for more information')

        
    
    def action_export_report(self, return_fp=False):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = "WHERE 1=1"
        query_where_sales = ""
        query_where_cancel = ""

        if self.start_date:
            query_where_sales += f" AND dso.date_order::date >= '{self.start_date}'" 
            query_where_cancel += f" AND tc.date >= '{self.start_date}'" 

        if self.end_date:
            query_where_sales += f" AND dso.date_order::date <= '{self.end_date}'" 
            query_where_cancel += f" AND tc.date <= '{self.end_date}'" 

        if self.sales_id:
            query_where += f" AND dso.sales_id = {self.sales_id.id}"

        if self.sales_coordinator_id:
            query_where += f" AND dso.sales_coordinator_id = {self.sales_coordinator_id.id}"

        if self.state_options in ['sale','done','cancel']:
            query_where += f" AND dso.state = '{self.state_options}'"
        elif self.state_options == 'progress_done_cancelled' :
            query_where += " AND dso.state in ('sale', 'done', 'cancel')"
        elif self.state_options == 'progress_done' :
            query_where += " AND dso.state in ('sale','done')"
        
        if self.company_ids:
            query_where += f" AND dso.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND dso.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.finco_ids:
            query_where += f" AND dso.finco_id IN {str(tuple([f.id for f in self.finco_ids])).replace(',)', ')')}"

        if self.product_ids:
            query_where += f" AND dsol.product_id IN {str(tuple([p.id for p in self.product_ids])).replace(',)', ')')}"

        return self._get_data_report_detail_per_chassis_engine(query_where, query_where_sales, query_where_cancel, return_fp)


    def _get_data_report_detail_per_chassis_engine(self, query_where, query_where_sales, query_where_cancel, return_fp=False):
        # Define report type handlers
        report_handlers = {
            'all': self._get_detail_select_query,
            'konsumen': self._get_select_consumen_query,
            'salesman': self._get_detail_select_query
        }

        # Get the appropriate query method based on report type
        query_method = report_handlers.get(self.report_type, self._get_detail_select_query)

        select_cancel = """
            tc.name as "Nomor Batal", 
            tc.date as "Tanggal Batal",
            regexp_replace(coalesce(tc.reason, ''), '[\n\r]+', ' ', 'g') as "Alasan Batal",
        """
        
        select_cancel_state_sale = """
            '' as "Nomor Batal", 
            Null as "Tanggal Batal",
            '' as "Alasan Batal",
        """

        query_join_cancel = """
            LEFT JOIN tw_dealer_sale_order_cancel dsoc on dsoc.dealer_sale_order_id = dso.id 
            LEFT JOIN tw_cancellation tc on tc.id = dsoc.cancellation_id and tc.state = 'confirmed'
        """
        
        query_where_cancel += " AND dsoc.id IS NOT NULL"

        # Digunakan untuk Laporan Penjualan Salesman
        factor_t = 0 if self.report_type == 'salesman' else 1

        if self.state_options in ('all','progress_done_cancelled','cancel'):
            # Get cancelled orders query
            query_select_cancel = query_method(factor=-1, factor_t=factor_t, query_select_cancel=select_cancel)
            query_cancel = self._get_detail_base_query(query_select_cancel, query_join_cancel, query_where, '', query_where_cancel)

            if self.state_options in ('all', 'progress_done_cancelled'):
                query_select_sales = query_method(factor=1, factor_t=factor_t, query_select_cancel=select_cancel_state_sale) 
                query_sales = self._get_detail_base_query(query_select_sales, '', query_where, query_where_sales, '')

                query = """
                    SELECT * 
                    FROM (({query_sales}) UNION ({query_cancel})) a
                    ORDER BY "Branch Code", "Date"
                """.format(query_sales=query_sales, query_cancel=query_cancel)
            else:
                query = query_cancel
        else:
            query_select_sales = query_method(factor=1, factor_t=factor_t, query_select_cancel=select_cancel_state_sale)
            query = self._get_detail_base_query(query_select_sales, '', query_where, query_where_sales, '')
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        if not result:
            raise Warning('Tidak ada data untuk di export')
                
        return self.env['web.report'].sudo().generate_report('Report Penjualan', result, show_total_footer=True, return_fp=return_fp)

    def _get_detail_base_query(self, query_select, query_join_cancel, query_where, query_where_sale, query_where_cancel):

        base_query = """
            {query_select}
            FROM tw_dealer_sale_order dso
            JOIN status s on 1=1
            JOIN status_t ts on 1=1
            LEFT JOIN tw_dealer_sale_order_line dsol on dsol.order_id = dso.id 
            {query_join_cancel}
            LEFT JOIN tw_dealer_sale_order_line_tax_rel as dsot on dsot.order_line_id = dsol.id
            left join tw_dealer_sale_order_summary dsos on dsos.order_id = dso.id and dsos.product_id = dsol.product_id
            LEFT JOIN account_tax as tax on tax.id = dsot.tax_id
            LEFT JOIN res_company b ON dso.company_id = b.id 
            LEFT JOIN tw_branch_setting bst ON bst.id = b.branch_setting_id 
            LEFT JOIN res_partner md ON b.default_supplier_id = md.id 
            LEFT JOIN res_area wba_area_1 ON bst.region_id = wba_area_1.id 
            LEFT JOIN res_area wba_area_2 ON bst.region_categ_id = wba_area_2.id 
            LEFT JOIN hr_employee hr_manager ON bst.area_manager_id = hr_manager.id
            LEFT JOIN res_partner finco ON dso.finco_id = finco.id 
            LEFT JOIN resource_resource sales ON dso.user_id = sales.user_id 
            LEFT JOIN hr_employee hr_sales ON dso.sales_id = hr_sales.id 
            LEFT JOIN hr_job job ON hr_sales.job_id = job.id 
            LEFT JOIN hr_employee hr_sales_koor ON dso.sales_coordinator_id = hr_sales_koor.id
            LEFT JOIN hr_job sales_koor_job ON hr_sales_koor.job_id = sales_koor_job.id 
            LEFT JOIN res_partner cust ON dso.partner_id = cust.id 
            LEFT JOIN product_product product ON dsol.product_id = product.id 
            LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id 
            LEFT JOIN product_variant_combination variant ON product.id = variant.product_product_id
            LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id 
            INNER join product_attribute atr on atr.id = attr.attribute_id and atr.name->>'en_US' in ('Color','Warna')
            LEFT JOIN product_attribute_value pav ON attr.product_attribute_value_id = pav.id
            LEFT JOIN product_series prod_series ON prod_template.series_id = prod_series.id 
            LEFT JOIN product_category prod_category ON prod_template.categ_id = prod_category.id 
            LEFT JOIN product_category prod_category2 ON prod_category.parent_id = prod_category2.id 
            LEFT JOIN stock_lot lot ON dsol.lot_id = lot.id 
            LEFT JOIN res_partner stnk ON lot.customer_stnk_id = stnk.id
            LEFT JOIN res_partner bj ON dsol.biro_jasa_id = bj.id
            LEFT JOIN res_city city ON stnk.city_id = city.id
            LEFT JOIN res_district kec ON stnk.district_id = kec.id
            LEFT JOIN tw_faktur_pajak_out fp ON dso.faktur_pajak_id = fp.id 
            LEFT JOIN stock_location source_loc ON source_loc.id = dso.sales_source_location_id 
            LEFT JOIN ( 
                SELECT order_line_id,
                    sum(amount_ahm) as amount_ahm,
                    sum(case when amount_ahm > 0 or amount_md > 0 or amount_dealer > 0 then discount_customer else 0 end) as amount_md_cust, 
                    sum(case when amount_finco > 0 then discount_customer else 0 end) as amount_finco_cust
                FROM tw_dealer_sale_order_line_program "order" 
                GROUP BY order_line_id 
            ) dsol_disc ON dsol_disc.order_line_id = dsol.id
            LEFT JOIN (
                SELECT head.company_id,
                    line.ring_id,
                    line.district_id
                FROM tw_ring_kecamatan_line line
                LEFT JOIN tw_ring_kecamatan head ON head.id = line.ring_kecamatan_id
            ) ring ON ring.company_id=b.id and ring.district_id=kec.id
            LEFT JOIN tw_ring mr ON ring.ring_id=mr.id
            LEFT JOIN (
                SELECT order_line_id,
                    sum(unit_price) as total_brg_bonus,
                    sum(direct_gift_dealer) as total_bb_dealer
                FROM tw_dealer_sale_order_line_direct_gift 
                GROUP BY order_line_id 
            ) dsol_brg_bonus ON dsol_brg_bonus.order_line_id = dsol.id
            LEFT JOIN stock_location loc_stock ON loc_stock.id = dsol.location_id
            LEFT JOIN tw_master_act_type sp ON sp.id = dso.act_type_id
            LEFT JOIN tw_activity_atl_btl_line spal ON spal.id = dso.activity_plan_id 
            LEFT JOIN stock_location loc_tk ON loc_tk.id = spal.location_id
            LEFT JOIN tw_titik_keramaian tk ON tk.id = dso.activity_point_id 
            LEFT JOIN stock_location src_pos ON src_pos.id = spal.source_pos_location_id
            LEFT JOIN tw_selection sales_chan ON sales_chan.id = dso.sales_channel_id
            LEFT JOIN tw_selection payment ON payment.id = dso.payment_type_id
            {query_where}
            {query_where_sale}
            {query_where_cancel}
            ORDER BY b.code, dso.date_order
        """.format(query_select=query_select, query_join_cancel=query_join_cancel, query_where=query_where, query_where_sale=query_where_sale, query_where_cancel=query_where_cancel)

        return base_query

    def _get_detail_select_query(self, factor=1, factor_t=1, query_select_cancel=''):
        query_select_sale = """
            WITH status as (select {factor} as factor),
            status_t AS (SELECT {factor_t} AS factor_t)
            SELECT COALESCE(b.code,'') as "Branch Code", 
                COALESCE(b.name,'') as "Branch Name", 
                COALESCE(md.code,'') as "Main Dealer", 
                COALESCE(dso.name,'') as "SO Number", 
                CASE WHEN dso.state = 'sale' THEN 'Sales Order' 
                    WHEN dso.state = 'done' THEN 'Done' 
                    WHEN dso.state = 'cancel' THEN 'Cancelled'
                    WHEN dso.state IS NULL THEN '' 
                    ELSE dso.state 
                END as "State", 
                dso.date_order as "Date", 
                CASE WHEN payment.name = 'Cash' then 'Cash'
                    ELSE finco.code
                END as "Payment Type",
                CASE WHEN dso.is_cod = TRUE THEN 'COD' 
                    ELSE 'Reguler' 
                END as "Sales Type", 
                COALESCE(hr_sales_koor.name,'') as "Sales Coord Name", 
                COALESCE(sales_koor_job.name->>'en_US', '') as "Sales Coord Job Name", 
                COALESCE(hr_sales.registry_number,'') as "Sales NIP", 
                COALESCE(hr_sales.name,'') as "Sales Name", 
                COALESCE(job.name->>'en_US','') as "Job Name", 
                COALESCE(cust.code,'') as "Customer Code", 
                COALESCE(cust.name,'') as "Customer Name",  
                COALESCE(product.default_code,'') as "Type", 
                COALESCE(pav.code,'') as "Color", 
                s.factor * COALESCE(dsol.product_uom_qty,0) as "Qty", 
                COALESCE(lot.name,'') as "Engine Number",
                COALESCE(lot.chassis_number ,'') as "Chassis Number", 
                s.factor * COALESCE(dsol.price_unit,0) as "Off The Road\n(A)", 
                s.factor * COALESCE(dsol.discount_regular,0) as "Discount PO\n(B)", 
                s.factor * COALESCE(dsol.amount_subsidy_dealer,0) as "PS Dealer\n(C)", 
                s.factor * COALESCE(dsol_disc.amount_ahm,0) as "PS AHM\n(D)", 
                s.factor * COALESCE(dsol.amount_subsidy_md,0) as "PS MD\n(E)", 
                s.factor * COALESCE(dsol.amount_subsidy_finco,0) as "PS Finco\n(F)", 
                s.factor * COALESCE(dsol.amount_subsidy,0) as "PS Total\n(G = C + D + E + F)", 
                s.factor * COALESCE(dsol_disc.amount_md_cust, 0) as "Discount Real (PS MD)\n(H)", 
                s.factor * COALESCE(dsol_disc.amount_finco_cust, 0) as "Discount Real (PS Finco)\n(I)", 
                s.factor * COALESCE(dsos.price_unit_untaxed, 0) as "Nett Sales\n(J = A/0.11)", 
                (s.factor * ts.factor_t) * ROUND(COALESCE(dsol.discount_regular / (1 + (COALESCE(tax.amount,0)/100)), 0)::numeric, 2) as "Total Disc Reg (Nett)\n(K = B/1.1)", 
                (s.factor * ts.factor_t) * ROUND(COALESCE(dsol.amount_subsidy / (1 + (COALESCE(tax.amount,0)/100)), 0)::numeric, 2) as "Total Disc PS (Nett)\n(L = (H + I)/1.1)", 
                (s.factor * ts.factor_t) * COALESCE(dso.amount_discount_total, 0) as "Total Disc\n(M = K + L)",         
                (s.factor * ts.factor_t) * COALESCE(dsol.price_subtotal,0) as "DPP\n(N = J - M)",
                (s.factor * ts.factor_t) * ROUND(COALESCE(dsol.price_tax, 0)::numeric, 2) as "PPN\n(O = N * Tax)",
                (s.factor * ts.factor_t) * COALESCE(lot.cogs, 0) as "HPP\n(P)",
                s.factor * COALESCE(dso.amount_downpayment, 0) as "Piutang DP\n(Q)",
                s.factor * COALESCE(dso.amount_receivable, 0) as "Piutang\n(R = N + O - Q + T)",
                (s.factor * ts.factor_t) * ROUND(COALESCE(dso.amount_gp_unit,0)::numeric, 2) as "GP Unit\n(S = N - P + (D + E + F))",  
                s.factor * COALESCE(dsol.bbn_amount, 0) as "Sales BBN\n(T)",
                (s.factor * ts.factor_t) * COALESCE(dsol.bbn_force_cogs, 0) as "HPP BBN\n(U = Z + AC + AD)",
                (s.factor * ts.factor_t) * ROUND(COALESCE(dso.amount_gp_bbn, 0)::numeric, 2) as "GP BBN\n(V = R - U - AE)", 
                (s.factor * ts.factor_t) * ROUND((COALESCE(dso.amount_gp_unit,0) + COALESCE(dso.amount_gp_bbn, 0))::numeric, 2) as "Total GP\n(W = S + V)",
                s.factor * COALESCE(dsol.amount_commission, 0) as "Hutang Komisi\n(X)", 
                s.factor * COALESCE(dsol.amount_extra_reward, 0) as "Extra Reward\n(Y)", 
                (s.factor * ts.factor_t) * COALESCE(dsol.finco_incentive, 0) as "DPP Insentif Finco", 
                -- TODO?: Insentif Finco blum terpakai di existing Teds, jika perlu bisa dibuka
                -- COALESCE(dsol.finco_incentive * (COALESCE(tax.amount,0)/100), 0) as "Insentif Finco", 
                (s.factor * ts.factor_t) * COALESCE(dso.amount_dealer_expense, 0) as "Beban Cabang", 
                COALESCE(dsol_brg_bonus.total_brg_bonus, 0) as "Total Barang Bonus\n(Z)", 
                COALESCE(prod_category.name, '') as "Category Name", 
                COALESCE(prod_category2.name, '') as "Parent Category Name", 
                COALESCE(prod_series.name->>'en_US', '') as "Series", 
                COALESCE(fp.name, '') as "Faktur Pajak", 
                COALESCE((dso.date_order::date - lot.receive_date::date)::integer, 0) as "Umur Stock", 
                city.code as "Kode Kabupaten", 
                city.name as "Kabupaten", 
                kec.code as "Kode Kecamatan", 
                kec.name as "Kecamatan", 
                sp.name as "Jaringan Penjualan", 
                sales_chan.name as "Sumber Penjualan", 
                tk.name as "Titik Keramaian", 
                loc_tk.name as "Source Location", 
                COALESCE(src_pos.name, source_loc.name, '') as "Source POS Location", 
                {query_select_cancel}
                COALESCE(hr_sales_koor.registry_number,'') as "Sales Coord NIP",
                COALESCE(cust.mobile,'') as "Customer Mobile",
                dsol.tenor as "Tenor",
                mr.name as "Ring",
                dsol.finco_po_number as "No PO\n(AA)",
                loc_stock.name as "Stock Location\n(AB)",
                s.factor * COALESCE(dsol.bbn_notice_amount, 0) as "Price BBN Notice\n(AC)",
                s.factor * COALESCE(dsol.bbn_process_amount, 0) as "Price PNBP dan STCK\n(AD)",
                s.factor * COALESCE(dsol.bbn_serv_amount, 0) as "Price BBN Jasa\n(AE)",
                s.factor * coalesce(dsol.bbn_taxed_amount, 0) as "Price BBN Jasa PPN\n(AF=(T - AB - AC) / (1 + tax amt) * tax amt)",
                s.factor * (COALESCE(dsol_disc.amount_ahm,0) + COALESCE(dsol.amount_subsidy_md,0)) as "SCP(Include PPN)\n(AG = D + E)",
                s.factor * (COALESCE(dsol_disc.amount_ahm,0) + COALESCE(dsol.amount_subsidy_md,0))/(1 + (COALESCE(tax.amount,0)/100)) as "SCP(Exclude PPN)\n(AH=(D + E)/1,11)",
                COALESCE(cust.identification_number, '') as "KTP Customer",
                COALESCE(stnk.identification_number, '') as "KTP Customer STNK",
                COALESCE(bj.name, '') as "Birojasa",
                COALESCE(wba_area_1.name, '') as "Area", 
                COALESCE(wba_area_2.name, '') as "Area 2", 
                COALESCE(hr_manager.name, '') as "AM", 
                (s.factor * ts.factor_t) * (COALESCE(dsol.discount_regular,0) 
                    + COALESCE(dso.amount_downpayment, 0) 
                    + COALESCE(dsol.amount_subsidy_dealer,0) 
                    + COALESCE(dsol_disc.amount_ahm,0) 
                    + COALESCE(dsol.amount_subsidy_md,0) 
                    + COALESCE(dsol.amount_subsidy_finco,0)) as "DP Sistem\n(AI = B + Q + C + D + E + F)",
                (s.factor * ts.factor_t) * COALESCE(dso.amount_downpayment, 0) as "DP Bayar\n(AJ = O)",
                (s.factor * ts.factor_t) * (COALESCE(dsol.price_unit,0) + COALESCE(dsol.bbn_amount, 0)) as "OTR\n(AK = A + T)", 
                CASE 
                    WHEN (COALESCE(dsol.price_unit, 0) + COALESCE(dsol.bbn_amount, 0)) != 0 THEN
                        ROUND(
                            ((
                                COALESCE(dsol.discount_regular, 0) 
                                + COALESCE(dso.amount_downpayment, 0) 
                                + COALESCE(dsol.amount_subsidy_dealer, 0) 
                                + COALESCE(dsol_disc.amount_ahm, 0) 
                                + COALESCE(dsol.amount_subsidy_md, 0) 
                                + COALESCE(dsol.amount_subsidy_finco, 0)
                            ) / (COALESCE(dsol.price_unit, 0) + COALESCE(dsol.bbn_amount, 0)) * 100)::numeric
                        , 2)::text || '%'
                    ELSE '0%'
                END AS "% DP Sistem\n(AL = AG / AI)",
                CASE 
                    WHEN (COALESCE(dsol.price_unit, 0) + COALESCE(dsol.bbn_amount, 0)) != 0 THEN
                        ROUND((
                            (COALESCE(dso.amount_downpayment, 0) 
                            / (COALESCE(dsol.price_unit, 0) + COALESCE(dsol.bbn_amount, 0))) 
                            * 100)::numeric 
                        , 2)::text || '%'
                    ELSE '0%'
                END AS "% DP Bayar\n(AM = AH / AI)",
                s.factor * COALESCE(dsol.amount_subsidy_diff_md, 0) as "PS MD Diff\n(AN)", 
                s.factor * COALESCE(dsol.amount_subsidy_diff_finco, 0) as "PS Finco Diff\n(AO)", 
                s.factor * COALESCE(dsol.amount_voucher, 0) AS "Voucher\n(AP)",
                s.factor * (COALESCE(dsos.price_unit_untaxed - COALESCE(lot.cogs, 0) - COALESCE(dso.amount_dealer_expense, 0), 0) 
                    + COALESCE(dso.amount_gp_bbn, 0) 
                    + COALESCE(dsol.amount_subsidy_diff_md, 0) 
                    + COALESCE(dsol.amount_subsidy_diff_finco, 0)) as "SISA MARGIN\n(AQ=(J - P - B - C - X - Y - Z) + V + AN + AO)"
        """.format(factor=factor, factor_t=factor_t, query_select_cancel=query_select_cancel)

        return query_select_sale
    
    def _get_select_consumen_query(self, factor=1, factor_t=1, query_select_cancel=None):

        query_select_sale_consumen = """
            WITH status as (select {factor} as factor),
            status_t AS (SELECT {factor_t} AS factor_t)
            SELECT COALESCE(b.code,'') as "Branch Code", 
                COALESCE(b.name,'') as "Branch Name", 
                COALESCE(md.code,'') as "Main Dealer", 
                COALESCE(dso.name,'') as "SO Number", 
                CASE WHEN dso.state = 'sale' THEN 'Sales Order' 
                    WHEN dso.state = 'done' THEN 'Done' 
                    WHEN dso.state = 'cancel' THEN 'Cancelled'
                    WHEN dso.state IS NULL THEN '' 
                    ELSE dso.state 
                END as "State", 
                dso.date_order as "Date", 
                CASE WHEN payment.name = 'Cash' then 'Cash'
                    ELSE finco.code
                END as "Payment Type",
                CASE WHEN dso.is_cod = TRUE THEN 'COD' 
                    ELSE 'Reguler' 
                END as "Sales Type", 
                COALESCE(hr_sales_koor.name,'') as "Sales Coord Name", 
                COALESCE(hr_sales.registry_number,'') as "Sales NIP", 
                COALESCE(hr_sales.name,'') as "Sales Name", 
                COALESCE(job.name->>'en_US','') as "Job Name", 
                COALESCE(cust.code,'') as "Customer Code", 
                COALESCE(cust.name,'') as "Customer Name",  
                COALESCE(product.default_code,'') as "Type", 
                COALESCE(pav.code,'') as "Color", 
                s.factor * COALESCE(dsol.product_uom_qty,0) as "Qty", 
                COALESCE(lot.name,'') as "Engine Number",
                COALESCE(lot.chassis_number ,'') as "Chassis Number", 
                s.factor * COALESCE(dsol.price_unit,0) as "Off The Road\n(A)", 
                s.factor * COALESCE(dsol.discount_regular,0) as "Discount PO\n(B)", 
                s.factor * COALESCE(dsol.amount_subsidy_dealer,0) as "PS Dealer\n(C)", 
                s.factor * COALESCE(dsol_disc.amount_ahm,0) as "PS AHM\n(D)", 
                s.factor * COALESCE(dsol.amount_subsidy_md,0) as "PS MD\n(E)", 
                s.factor * COALESCE(dsol.amount_subsidy_finco,0) as "PS Finco\n(F)", 
                s.factor * COALESCE(dsol.amount_subsidy,0) as "PS Total\n(G = C + D + E + F)", 
                s.factor * COALESCE(dsos.price_unit_untaxed, 0) as "Nett Sales\n(H = A/0.11)", 
                s.factor * ROUND(COALESCE(dsol.discount_regular / (1 + (COALESCE(tax.amount,0)/100)), 0)::numeric, 2) as "Total Disc Reg (Nett)\n(I = B/1.1)", 
                s.factor * ROUND(COALESCE(dsol.amount_subsidy / (1 + (COALESCE(tax.amount,0)/100)), 0)::numeric, 2) as "Total Disc PS (Nett)\n(J = (H + I)/1.1)", 
                s.factor * COALESCE(dso.amount_discount_total, 0) as "Total Disc\n(K = I + J)",         
                s.factor * COALESCE(dsol.price_subtotal,0) as "DPP\n(L = H - K)",
                s.factor * ROUND(COALESCE(dsol.price_tax, 0)::numeric, 2) as "PPN\n(M = L * Tax)",
                s.factor * COALESCE(lot.cogs, 0) as "HPP\n(N)",
                s.factor * COALESCE(dso.amount_downpayment, 0) as "Piutang DP\n(O)",
                s.factor * COALESCE(dso.amount_receivable, 0) as "Piutang\n(P = L + M - O)",
                s.factor * ROUND(COALESCE(dso.amount_gp_unit,0)::numeric, 2) as "GP Unit\n(Q = L - N)",  
                s.factor * COALESCE(dsol.bbn_amount, 0) as "Sales BBN\n(R)",
                s.factor * COALESCE(dsol.bbn_force_cogs, 0) as "HPP BBN\n(S)",
                s.factor * ROUND(COALESCE(dso.amount_gp_bbn, 0)::numeric, 2) as "GP BBN\n(T = R - S)", 
                s.factor * ROUND((COALESCE(dso.amount_gp_unit,0) + COALESCE(dso.amount_gp_bbn, 0))::numeric, 2) as "Total GP\n(U = Q + T)",
                s.factor * COALESCE(dsol.finco_incentive, 0) as "DPP Insentif Finco\n(V)", 
                s.factor * COALESCE(dso.amount_dealer_expense, 0) as "Beban Cabang\n(X)", 
                COALESCE(dsol_brg_bonus.total_brg_bonus, 0) as "Total Barang Bonus", 
                COALESCE(prod_category.name, '') as "Category Name", 
                COALESCE(prod_category2.name, '') as "Parent Category Name", 
                COALESCE(prod_series.name->>'en_US', '') as "Series", 
                COALESCE(fp.name, '') as "Faktur Pajak", 
                COALESCE((dso.date_order::date - lot.receive_date::date)::integer, 0) as "Umur Stock", 
                city.code as "Kode Kabupaten", 
                city.name as "Kabupaten", 
                kec.code as "Kode Kecamatan", 
                kec.name as "Kecamatan", 
                sp.name as "Jaringan Penjualan", 
                sales_chan.name as "Sumber Penjualan", 
                tk.name as "Titik Keramaian", 
                loc_tk.name as "Source Location", 
                COALESCE(src_pos.name, source_loc.name, '') as "Source POS Location", 
                {select_cancel_query}
                COALESCE(hr_sales_koor.registry_number,'') as "Sales Coord NIP",
                COALESCE(cust.mobile,'') as "Customer Mobile",
                dsol.tenor as "Tenor",
                mr.name as "Ring",
                dsol.finco_po_number as "No PO",
                loc_stock.name as "Stock Location",
                COALESCE(dsol.bbn_notice_amount, 0) as "Price BBN Notice",
                COALESCE(dsol.bbn_process_amount, 0) as "Price BBN Proses",
                COALESCE(dsol.bbn_serv_amount, 0) as "Price BBN Jasa",
                COALESCE(dsol.bbn_serv_area_amount, 0) as "Price BBN Area",
                COALESCE(dsol.bbn_capital_fee_amount, 0) as "Price BBN Fee Pusat",
                COALESCE(cust.identification_number, '') as "KTP Customer",
                COALESCE(stnk.identification_number, '') as "KTP Customer STNK"
        """.format(factor=factor, factor_t=factor_t, select_cancel_query=query_select_cancel)
        
        return query_select_sale_consumen
    
