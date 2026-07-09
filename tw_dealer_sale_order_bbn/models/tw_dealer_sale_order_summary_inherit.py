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
    bbn_amount = fields.Float('BBN Amount')
    bbn_purchase_amount = fields.Float('BBN Purchase Amount')
    bbn_taxed_amount = fields.Float('BBN Tax Amount')
    gross_profit_bbn = fields.Float('GP BBN')
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_gp(self):
        self.ensure_one()
        gp = super()._get_gp()
        return gp + self.gross_profit_bbn