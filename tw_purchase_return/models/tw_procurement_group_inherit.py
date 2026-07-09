from odoo import models, fields, api, _

class SaleProcurementGroup(models.Model):
    _inherit = "procurement.group"

    purchase_return_id = fields.Many2one('tw.purchase.return', 'Purchase Return')