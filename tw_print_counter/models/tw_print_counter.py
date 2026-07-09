from odoo import models, fields


class JumlahCetak(models.Model):
    _name = "tw.print.counter"
    _description = "Jumlah Cetak"
    
    reason = fields.Char('Reason')

    transaction_id = fields.Integer(string='Transaction Id')
    print_counter = fields.Integer(string='Jumlah Cetak')
    
    report_id = fields.Many2one('ir.actions.report',string='Report')
    model_id = fields.Many2one('ir.model','Model')