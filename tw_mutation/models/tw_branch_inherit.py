from odoo import models, fields, api

class mutationOrderInherit(models.Model):
    _inherit = "res.company"

    def prepare_partner_vals(self,vals):
        partner_vals = super().prepare_partner_vals(vals)
        partner_vals['route_type'] = 'internal'
        return partner_vals