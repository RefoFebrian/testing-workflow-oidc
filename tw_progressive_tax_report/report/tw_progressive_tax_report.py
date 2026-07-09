# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time,timedelta
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwProgressiveTaxReport(models.TransientModel):
    _name = "tw.progressive.tax.report"
    _description = "TW Progressive Tax Report"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now().date()

    # 8: fields
    name = fields.Char('Filename')
    file_excel = fields.Binary('File Excel')
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date',default=_get_default_date)
    state = fields.Selection([
        ('outstanding', 'Outstanding'),
        ('paid', 'Paid'),
        ('all', 'All')
    ], default='outstanding')

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_progressive_tax_report_company_rel', 'report_id', 'company_id')

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        start_date = self.start_date
        end_date = self.end_date
        state = self.state
        company_ids = self.company_ids.ids
        
        query_where = " WHERE pp.state = 'confirmed'"
        if company_ids:
            query_where += " AND b.id in %s "%(str(tuple(company_ids)).replace(',)', ')'))
        if start_date:
            query_where += " AND pp.date >= '%s'"%(start_date)
        if end_date:
            query_where += " AND pp.date <= '%s'"%(end_date)
        if state == 'outstanding':
            query_where += " AND ai.state != 'paid'"
        elif state == 'paid':
            query_where += " AND ai.state = 'paid'"
        
        query = """
            SELECT b.code as branch_code
            , b.name as branch_name
            , lot.name as engine
            , lot.chassis_number as chassis
            , so.name as no_so
            , p.name as partner_name
            , p.code as partner_code
            , p.mobile as no_telp
            , hr.name as sales
            , hr2.name  as koordinator
            , ai.name as no_invoce
            , ai.invoice_date 
            , ai.invoice_date_due
            , ROUND(
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - (ai.invoice_date + INTERVAL '7 hours'))) / 86400,
                2) as overdue
            , ai.amount_total
            , ai.state
            FROM tw_progressive_tax pp
            INNER JOIN tw_progressive_tax_line ppl ON ppl.progressive_tax_id = pp.id
            INNER JOIN stock_lot lot ON lot.id = ppl.lot_id
            INNER JOIN res_company b ON b.id = lot.company_id
            INNER JOIN tw_dealer_sale_order so ON so.id = lot.dealer_sale_order_id
            INNER JOIN account_move ai ON ai.id = lot.inv_progressive_tax_id
            INNER JOIN res_partner p ON p.id = lot.customer_stnk_id
            INNER JOIN hr_employee hr ON hr.resource_id = so.sales_id
            INNER JOIN hr_employee hr2 ON hr2.resource_id = so.sales_coordinator_id
        """
        query += query_where
        self._cr.execute(query)
        ress = self._cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report('Report Progressive Tax',ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    
