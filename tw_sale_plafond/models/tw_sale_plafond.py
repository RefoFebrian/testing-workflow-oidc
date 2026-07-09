from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
import inspect

class InheritSaleOrder(models.Model):
    _inherit = "tw.sale.order"
    _description = "Sale Order"

    credit_limit = fields.Float(string='Credit Limit', digits='Product Price')
    plafond_avaibility = fields.Float('Plafond Avaibility', digits='Product Price', compute='_compute_plafond_avaibility', recompute=True)

    @api.onchange('partner_id', 'division')
    def onchange_credit_limit_and_plafond(self):
        if self.partner_id and self.division:
            credit_limit = 0.0
            if 'credit_limit_sparepart' and 'credit_limit_unit' in self.partner_id._fields:
                credit_limit = self.partner_id.credit_limit_unit if self.division == 'Unit' else self.partner_id.credit_limit_sparepart

            self.credit_limit = credit_limit

    @api.depends('partner_id', 'state')
    def _compute_plafond_avaibility(self):
        for record in self:
            if record.division in ['Unit','Sparepart'] and record.state not in ('progress', 'unused'):
                record.plafond_avaibility = record.action_set_plafond_avaibility()

    def action_set_plafond_avaibility(self):
        self.onchange_credit_limit_and_plafond()
        return self.credit_limit - self.amount_invoiced 
    
    def _validate_order(self):
        partner_category = [categ.name for categ in self.partner_id.category_id]
        if 'Dealer' in partner_category:
            self.onchange_credit_limit_and_plafond()
            self._compute_plafond_avaibility()
            if round(self.amount_total, 2) > round(self.plafond_avaibility, 2):
                raise Warning(f"Cannot confirm! Order Total exceeds the Plafond Avaibility: {self.plafond_avaibility}. Current total: {self.amount_total}.")
        return super()._validate_order()