from datetime import datetime
from odoo import models, fields, api, _


class PrintStockOpnameUnitValidation(models.AbstractModel):
    _name = "report.tw_stock_opname.unit_validation"
    _description = "Report Stock Opname Unit Validation"
    
    def print_datetime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_previous_stock_opname(self):
        active_ids = self.env.context.get('active_ids', [])
        so = self.env['tw.stock.opname']
        curr = so.browse(active_ids)
        prev = so.search([('id', '!=', curr.id),
                          ('company_id', '=', curr.id),
                          ('state', '=', 'done')
                          ], order='id DESC', limit=1)
        return prev

    def get_previous_stock_opname_line(self, line):
        prev_so = self.get_previous_stock_opname()
        return prev_so.detail_accessories_ids.filtered(lambda l: l.product_id == line.product)    

    def diff(self, line):
        return line.qty_system - line.qty_good + line.qty_not_good

    def not_good_diff_from_previous_so(self, line):
        prev_so_line = self.get_previous_stock_opname_line(line)
        return line.qty_not_good - prev_so_line.qty_not_good

    def diff_from_previous_so(self, line):
        prev_so_line = self.get_previous_stock_opname_line(line)
        return self.diff(prev_so_line)

    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.stock.opname'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.stock.opname',
            'docs': docs,
            'print_datetime': self.print_datetime,
            'not_good_diff_from_previous_so': self.not_good_diff_from_previous_so,
            'diff': self.diff,
            'diff_from_previous_so': self.diff_from_previous_so,
        }