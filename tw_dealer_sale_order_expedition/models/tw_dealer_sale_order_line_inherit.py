# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from ast import Store
from signal import valid_signals
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderLineBBN(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    # 7: defaults methods

    # 8: fields
    accrue_expedition = fields.Float('Accrue Ekspedisi','_compute_expedition_amount', store=True)
    
    # 9: relation fields
    
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('company_id','product_id')
    def _compute_expedition_amount(self):
        for line in self:
            if line.company_id:
                account_conf = line.company_id.branch_setting_id.account_setting_id
                if account_conf.is_accrue_expedition and account_conf.accrue_expedition:
                    line.accrue_expedition = account_conf.accrue_expedition
                else:
                    line.accrue_expedition = 0
            else:
                line.accrue_expedition = 0
    
    # 12: override methods
    
    # 13: action methods
	
    # 14: private methods
    def _get_gp_additional_price(self):
        self.ensure_one()
        price = super()._get_gp_additional_price()
        price += self.accrue_expedition
        return price