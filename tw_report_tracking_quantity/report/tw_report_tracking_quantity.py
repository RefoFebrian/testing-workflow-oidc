# 1: imports of python lib
from datetime import timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError


# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwReportTrackingQuantity(models.TransientModel):
    _name = "tw.report.tracking.quantity"
    _description = "Report Tracking Quantity"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='End Date', default=fields.Date.context_today, required=True)
    division = fields.Selection([('Unit', 'Unit'), ('Sparepart', 'Sparepart')], string='Division', required=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise UserError(_('End Date harus lebih besar dari Start Date.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _get_where_clause(self):
        query_where = ""
        if self.company_ids:
            if len(self.company_ids) == 1:
                query_where += " AND branch.id = %s " % self.company_ids.id
            else:
                query_where += " AND branch.id in %s " % str(tuple(self.company_ids.ids))
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND branch.id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.start_date:
            query_where += " AND so.date_order >= '%s' " % self.start_date
        if self.end_date:
            query_where += " AND so.date_order <= '%s' " % self.end_date
        if self.division:
            query_where += " AND so.division = '%s' " % self.division
        return query_where

    def action_print_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = self._get_where_clause()

        query = """
            SELECT 
                branch.name AS "Branch Name",
                so.name AS "No Sale Order",
                CASE 
                    WHEN so.state = 'draft' THEN 'Draft'
                    WHEN so.state = 'waiting_for_approval' THEN 'Waiting For Approval'
                    WHEN so.state = 'approved' THEN 'Approved'
                    WHEN so.state = 'sale' THEN 'Sales Order'
                    WHEN so.state = 'done' THEN 'Done'
                    WHEN so.state = 'cancel' THEN 'Cancelled'
                    WHEN so.state = 'sent' THEN 'Quotation Sent'
                    ELSE so.state
                END AS "Status",
                COALESCE(so_summary.qty_so, 0) AS "Qty SO",
                inv_summary.name AS "No Invoice",
                COALESCE(inv_summary.qty_inv, 0) AS "Qty Inv",
                STRING_AGG(pick_summary.no_sj, ', ') AS "No Surat Jalan",
                COALESCE(SUM(pick_summary.qty_sj), 0) AS "Qty SJ"
            FROM tw_sale_order so
            LEFT JOIN (
                SELECT soh.name, SUM(sol.product_uom_qty) qty_so 
                FROM tw_sale_order soh 
                LEFT JOIN tw_sale_order_line sol ON sol.order_id = soh.id
                GROUP BY soh.name
            ) so_summary ON so_summary.name = so.name
            LEFT JOIN (
                SELECT am.invoice_origin AS origin, am.name, SUM(aml.quantity) qty_inv 
                FROM account_move am 
                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                WHERE am.move_type = 'out_invoice' AND am.state = 'posted'
                AND aml.display_type = 'product'
                GROUP BY am.invoice_origin, am.name
            ) inv_summary ON so.name = inv_summary.origin
            LEFT JOIN (
                SELECT wsp.origin, wsp.name AS no_sj, SUM(wspl.quantity) qty_sj 
                FROM stock_picking wsp 
                LEFT JOIN stock_move wspl ON wspl.picking_id = wsp.id
                WHERE wsp.state NOT IN ('cancel', 'assigned')
                GROUP BY wsp.origin, wsp.name
            ) pick_summary ON so.name = pick_summary.origin
            LEFT JOIN res_company branch ON so.company_id = branch.id
            WHERE 1=1 %s
            GROUP BY branch.name, so.name, so.state, so_summary.qty_so, inv_summary.name, inv_summary.qty_inv
            ORDER BY branch.name, so.name
        """ % (query_where)

        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()

        return self.env['web.report'].generate_report(report_name='Tracking Quantity %s' % self.division, data=data, start_date=self.start_date, end_date=self.end_date, )
    
