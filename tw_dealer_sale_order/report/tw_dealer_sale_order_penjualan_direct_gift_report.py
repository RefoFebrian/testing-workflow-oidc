# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, timedelta
from math import e 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWDealerSaleOrderPenjualanDirectGiftReport(models.TransientModel):
    _name = "tw.dealer.sale.order.penjualan.direct.gift.report"
    _description = "TW Dealer Sale Order Penjualan Direct Gift Report"


    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    report_type = fields.Selection([
        ('',''),
        ('all','Penjualan Direct Gift'),
        ('salesman','Salesman'),], string='Report Type', default='all', help="Pilih tipe laporan penjualan direct gift : \nPenjualan Direct Gift: Laporan Penjualan Direct Gift\nSalesman: Laporan Penjualan Direct Gift Salesman\n\nTiap tipe laporan memerlukan access group tersendiri, apabila tidak punya access harap hubungi pihak Helpdesk")

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
    
    company_ids = fields.Many2many('res.company','tw_dso_penjualan_dg_company_rel', 'report_id', 'company_id', string="Branch")
    product_ids = fields.Many2many('product.product', 'tw_dso_report_penjualan_dg_product_rel', 'report_id', 'product_id', string='Product')
    finco_ids = fields.Many2many('res.partner', 'tw_dso_report_penjualan_dg_finco_rel', 'report_id', 'finco_id', string='Finco')

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise Warning('Start Date must be less than End Date')

    @api.onchange('report_type')
    def onchange_report_type(self):
        if self.report_type == 'salesman':
            user_access = self.env.user.has_group('tw_dealer_sale_order.group_tw_dso_report_sales_direct_gift_salesman_read')
            if not user_access:
                raise Warning('You do not have access to this report type\n\nPlease contact your helpdesk for more information')
        elif self.report_type == 'all':
            user_access = self.env.user.has_group('tw_dealer_sale_order.group_tw_dso_report_sales_direct_gift_all_read')
            if not user_access:
                raise Warning('You do not have access to this report type\n\nPlease contact your helpdesk for more information')

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = "WHERE 1=1"
        query_where_sales = ""
        query_where_cancel = ""

        if self.start_date:
            query_where_sales += f" AND dso.date_order >= '{self.start_date}'" 
            query_where_cancel += f" AND tc.date >= '{self.start_date}'" 

        if self.end_date:
            query_where_sales += f" AND dso.date_order <= '{self.end_date}'" 
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

        return self._get_data_report_direct_gift(query_where, query_where_sales, query_where_cancel)


    def _get_data_report_direct_gift(self, query_where, query_where_sales, query_where_cancel=None):

        query = """
            select 
                rc.code as "Branch Code"
                , rc.name as "Branch Name"
                , dso.name as "No Sale Order"
                , dso.state as "State"
                , dso.date_order as "Date"
                , rr.name as "FLP Type"
                , job.name->>'en_US' as "FLP Name"
                , rps.code as "Customer Code"
                , rps.name as "Customer Name"
                , pt.name->>'en_US' as "Model Type"
                , pt.description as "Model Desc"
                , dsol.product_uom_qty as "Unit Qty"
                , lot.name as "Engine"
                , lot.chassis_number as "Chassis"
                , subar.name as "Direct Gift Code"
                , subprod.default_code as "Direct Gift Name"
                , bb.quantity as "Qty"
                , bb.unit_price as "Unit Price"
            from tw_dealer_sale_order dso
            LEFT JOIN tw_dealer_sale_order_line dsol on dsol.order_id = dso.id 
            LEFT JOIN tw_dealer_sale_order_line_direct_gift bb on bb.order_line_id = dsol.id
            LEFT JOIN res_company rc on dso.company_id = rc.id
            LEFT JOIN resource_resource rr on dso.user_id=rr.user_id
            LEFT JOIN hr_employee hre on hre.resource_id=rr.id
            LEFT JOIN hr_job job on hre.job_id=job.id
            LEFT JOIN res_partner rps on dso.partner_id=rps.id
            LEFT JOIN product_product pp on dsol.product_id=pp.id
            LEFT JOIN product_template pt on pp.product_tmpl_id=pt.id
            LEFT JOIN stock_lot lot on dsol.lot_id=lot.id
            LEFT JOIN tw_sales_program subar on bb.direct_gift_id = subar.id
            LEFT JOIN product_product subprod on bb.product_id = subprod.id
            {query_where}
            {query_where_sales}
        """.format(query_where=query_where, query_where_sales=query_where_sales)
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        if not result:
            raise Warning('Tidak ada data untuk di export')

        return self.env['web.report'].sudo().generate_report('Report Direct Gift By Sale Order', result, show_total_footer=False)
    