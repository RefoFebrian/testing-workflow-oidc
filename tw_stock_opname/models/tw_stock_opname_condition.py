from odoo import models, fields

class StockOpnameCondition(models.Model):
    _name = "tw.stock.opname.condition"
    _description = "Stock Opname Condition"

    other_information = fields.Char('Other Information')
    status_kondisi = fields.Selection([
        ('ada_baik', 'Ada Baik'),
        ('ada_rusak', 'Ada Rusak'),
        ('tidak_ada', 'Tidak Ada'),
    ], string='Status', readonly=True)
    code = fields.Char("Code", related='condition_id.value', store=True)

    location_id = fields.Many2one('tw.stock.opname.location', ondelete="cascade")
    accessories_location_id = fields.Many2one('tw.stock.opname.accessories.location', ondelete="cascade")
    condition_id =  fields.Many2one('tw.selection', string='Condition' , domain=[('type','=','SoCondition')])