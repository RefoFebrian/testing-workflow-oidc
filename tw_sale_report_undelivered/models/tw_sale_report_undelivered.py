from odoo import models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class SaleReportUndelivered(models.TransientModel):
    _name = "tw.sale.report.undelivered"
    _description = "SO Undelivered Report"

    def _get_default_date(self): 
        return datetime.now()

    options = fields.Selection([
        ('detail', 'Detail per Sales')
    ], string='Options', default='detail')

    start_date = fields.Date('Start Date', default=lambda self: self._get_default_date().replace(day=1))
    end_date = fields.Date('End Date', default=_get_default_date)

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    company_ids = fields.Many2many('res.company', 'tw_sale_report_undelivered_company_rel', 'report_so_undelivered_id', 'company_id', "Branch", copy=False, domain=[('parent_id','!=',False)])
    partner_ids = fields.Many2many('res.partner','tw_sale_report_undelivered_partner_rel','report_so_undelivered_id', 'partner_id', 'Suppliers')

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = """ 
            AND so.state = 'sale'
        """

        if self.company_ids:
            company_ids = str(tuple([b.id for b in self.company_ids])).replace(',)', ')')
            query_where += f" AND rc.id IN {company_ids}"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND rc.id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.partner_ids:
            partner_ids = str(tuple([p.id for p in self.partner_ids])).replace(',)', ')')
            query_where += f" AND partner.id IN {partner_ids}"

        if self.division:
            query_where += f" AND so.division = '{self.division}'"

        if self.start_date:
            query_where += f" AND so.date_order >= '{self.start_date}' "

        if self.end_date:
            query_where += f" AND so.date_order <= '{self.end_date}' "

        query = f"""
            SELECT 
                rc.code AS branch_code,
                so.name AS sale_order,
                so.division AS division,
                so.date_order + INTERVAL '7 hours' AS date_order,
                so.state AS state,
                partner.code AS partner_code,
                partner.name AS partner_name,
                prod.default_code AS product_code,
                sol.name AS description,
                sol.product_uom_qty AS product_qty,
                sol.price_unit AS price_unit,
                round(sol.price_unit / (1 + COALESCE(tax.amount,0)/100),2) AS nett_sales,
                sol.discount AS discount,
                round((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100)) / (1 + COALESCE(tax.amount,0)/100),2) AS dpp,
                round((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty),2) AS sub_total,
                COALESCE(sol.cogs, 0) AS force_cogs,
                sol.qty_delivered AS delivered_qty,
                ((sol.cogs ) * ( sol.qty_delivered )) as delivered_value,
                sol.cogs * sol.product_uom_qty AS total_hpp,
                sol.product_uom_qty - sol.qty_delivered AS qty_undelivered,
                COALESCE(sol.cogs, 0) * (sol.product_uom_qty - sol.qty_delivered) AS stock_undelivered
            FROM tw_sale_order so
                JOIN tw_sale_order_line sol ON so.id = sol.order_id
                LEFT JOIN account_tax_tw_sale_order_line_rel so_tax ON sol.id = so_tax.tw_sale_order_line_id 
                LEFT JOIN account_tax tax ON tax.id = so_tax.account_tax_id 
                JOIN res_company rc ON rc.id = so.company_id
                LEFT JOIN res_partner partner ON partner.id = so.partner_id
                LEFT JOIN product_product prod ON prod.id = sol.product_id
            WHERE sol.product_uom_qty != sol.qty_delivered
            {query_where}
            ORDER BY rc.code, so.date_order, so.name, prod.default_code;
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('SO Undelivered', result)
    