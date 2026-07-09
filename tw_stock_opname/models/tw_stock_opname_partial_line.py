from odoo import models, fields, api

class StockOpnamePartialLine(models.TransientModel):
    _name = "tw.stock.opname.partial.line"
    _description = "Wizard Stock Opname Partial Line"
    # TODO : Cek Domain, tidak berjalan dan masih error
    # def _domain_location(self):
    #     datas = self.partial_id.opname_id.get_stock_location()
    #     if datas : 
    #         domain = [('id','in',[data['location_id'] for data in datas])]
    #         return domain
        
    qty = fields.Integer(string='Quantity')
    line_type = fields.Selection([('unit', 'Unit'), ('accessory', 'Accessory')
    ], string='Type', default='unit')
    location_id = fields.Many2one('stock.location', string="Lokasi")
    partial_id = fields.Many2one('tw.stock.opname.partial', ondelete="cascade")