from odoo import models, fields
from datetime import datetime

class StockOpnameHistory(models.Model):
    _name = "tw.stock.opname.history"
    _description = "Stock Opname History"

    def _get_default_datetime(self):
        return datetime.now()

    count_date = fields.Datetime(string='Datetime')
    perhitungan_ke = fields.Integer(string='Perhitungan Ke', default=0)
    qty_count = fields.Integer(string='Qty')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('selisih', 'Selisih'),
        ('anomali', 'Anomali'),
        ('done', 'Done'),   
    ], string='Status', default='draft')

    employee_id = fields.Many2one('hr.employee', string='Penanggung Jawab')
    opname_detail_id = fields.Many2one('tw.stock.opname.detail', ondelete="cascade")