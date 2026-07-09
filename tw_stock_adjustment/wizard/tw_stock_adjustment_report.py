# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib


# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwStockAdjustmentReport(models.TransientModel):
    _name = "tw.stock.adjustment.report"
    _description = "Report Stock Adjustment"

    # 7: defaults methods
    def _get_company_ids(self):
        company_ids_user = self.env.user.company_ids
        company_ids = [b.id for b in company_ids_user]
        return company_ids

    def _set_domain_company_ids(self):
        return [('id', 'in', self.env.user.company_ids.ids), ('parent_id', '!=', False)]

    # 8: fields
    division = fields.Selection(
        selection=lambda self: self.env['tw.selection'].get_division_options(),
        string='Division',
        default='Sparepart'
    )
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date', default=fields.Date.today)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_stock_adjustment_report_branch_rel', 'tw_stock_adjustment_report_id',
                                    'company_id', 'Branch', copy=False, domain=_set_domain_company_ids)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def action_download(self):
        start_date = self.start_date
        end_date = self.end_date

        if len(self.company_ids) == 0:
            self.company_ids = self._get_company_ids()

        ress = self._print_excel_report()
        report_name = f"Report Stock Adjustment ({self.division or 'All'})"
        return self.env['web.report'].sudo().generate_report(report_name, ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    def _print_excel_report(self):
        branch_ids = self.company_ids.ids
        division = self.division
        start_date = self.start_date
        end_date = self.end_date

        query = """
            SELECT 
                rc.code AS "Branch Code",
                rc.name AS "Branch Name",
                tsa.name AS "Reference",
                sl.complete_name AS "Location",
                tsa.division AS "Division",
                tsa.state AS "State",
                tsa.date AS "Date",
                tsa.done_date + interval '7 hours' AS "Adjustment Date",
                COALESCE(pt.name->>'en_US', pt.name->>(SELECT key FROM jsonb_object_keys(pt.name) AS key LIMIT 1)) AS "Product Name",
                pp.default_code AS "Product Code",
                tsal.qty_system AS "Theoretical Qty",
                tsal.qty_counted AS "Counted Qty",
                (tsal.qty_counted - tsal.qty_system) AS "Difference",
                tsal.adjustment_cost AS "Unit Price"
            FROM tw_stock_adjustment tsa
            INNER JOIN tw_stock_adjustment_line tsal ON tsa.id = tsal.adjustment_id
            LEFT JOIN stock_location sl ON tsa.location_id = sl.id
            LEFT JOIN res_company rc ON tsa.company_id = rc.id
            LEFT JOIN product_product pp ON tsal.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        """

        query_where = """ 
            WHERE tsa.state = 'done'
        """

        if branch_ids:
            query_where += " AND rc.id IN %s " % str(tuple(branch_ids)).replace(',)', ')')
        if division:
            query_where += " AND tsa.division = '%s' " % division
        if start_date:
            query_where += " AND tsa.done_date >= '%s' " % start_date
        if end_date:
            query_where += " AND tsa.done_date <= '%s 23:59:59' " % end_date

        query_order = " ORDER BY tsa.done_date, tsa.name, tsal.id "

        self.env.cr.execute(query + query_where + query_order)
        ress = self.env.cr.dictfetchall()
        return ress
