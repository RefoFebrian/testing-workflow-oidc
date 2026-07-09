from odoo import models, fields, api, _


class InheritSaleOrder(models.Model):
    _inherit = "tw.sale.order"
    _description = "Sale Order"

    drawdown = fields.Float(string='Drawdown', digits='Product Price')

    @api.onchange('partner_id', 'division')
    def onchange_partner_drawdown(self):
        if self.partner_id and self.division:
            drawdown = 0.0
            if 'drawdown_sparepart' and 'drawdown_unit' in self.partner_id._fields:
                drawdown = self.partner_id.drawdown_unit if self.division == 'Unit' else self.partner_id.drawdown_sparepart

            self.drawdown = drawdown
    
    def action_set_plafond_avaibility(self):
        self.onchange_partner_drawdown()
        return super().action_set_plafond_avaibility() - self.drawdown