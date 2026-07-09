# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderSummary(models.Model):
    _inherit = "tw.dealer.sale.order.summary"
    _description = "Summary Discount Dealer Sales Order"

    # 7: defaults methods

    # 8: fields
    accrue_expedition = fields.Float('Accrue Expedition')
    
    # 9: relation fields