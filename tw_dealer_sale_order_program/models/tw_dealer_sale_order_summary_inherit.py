# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwDealerSaleOrderSummaryInherit(models.Model):
    _inherit = "tw.dealer.sale.order.summary"

    # 7: defaults methods

    # 8: fields
    amount_subsidy = fields.Float('Subsidi Program')
    amount_subsidy_dealer = fields.Float('Selisih Dealer')
    amount_subsidy_md = fields.Float('Selisih MD')
    amount_subsidy_finco = fields.Float('Selisih Finco')
    is_pilot_discount = fields.Boolean('Is Pilot Discount', compute='')

    def _get_discount(self):
        self.ensure_one()
        discount = super()._get_discount()
        is_pilot = self._is_dso_discount_pilot()
        if is_pilot:
            discount += self.amount_subsidy
        else:
            discount += self.amount_subsidy_dealer
        return discount
    
    def _is_dso_discount_pilot(self):
        is_pilot = False
        pilot = self.env['tw.pilot.project'].sudo().search([('name','=','Discount DSO'),('active','=',True)])
        if pilot:
            companies = pilot.company_ids.ids
            if companies:
                if self.order_id.company_id.id in companies:
                    is_pilot = True
        return is_pilot