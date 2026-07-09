# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Purchase Order'

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('purchase_order_type_id')
    def _onchange_payment_terms(self):
        for order in self:
            if order.purchase_order_type_id and order.purchase_order_type_id.payment_term_id:
                order.payment_term_id = order.purchase_order_type_id.payment_term_id