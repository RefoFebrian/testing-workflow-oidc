from odoo import models, _
from odoo.exceptions import UserError as Warning


class InheritSaleOrder(models.Model):
    _inherit = "tw.sale.order"
    # INFO : Override from Sale Order and Connected to Approval Module and Connected to Plafond'
    
    def action_rfa(self):
        if self.plafond_avaibility < self.amount_total and self.division == 'Unit':
            raise Warning(f"Attention! Plafond Availability ({self.plafond_avaibility}) is less than the Total Amount ({self.amount_total})!")
        return super().action_rfa()