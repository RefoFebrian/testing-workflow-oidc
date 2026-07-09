from odoo import models, fields


class InheritResPartner(models.Model):
    _inherit = "res.partner"
    
    drawdown_unit = fields.Float('Drawdown Unit', digits='Product Price')
    drawdown_sparepart = fields.Float('Drawdown Sparepart', digits='Product Price')