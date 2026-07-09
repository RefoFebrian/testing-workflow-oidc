# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from itertools import groupby

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrder(models.Model):
    _name = "tw.dealer.sale.order"
    _inherit = ['tw.dealer.sale.order', 'tw.approval.mixin']

    approval_ids = fields.One2many(comodel_name='tw.approval.line', inverse_name='transaction_id', string="Table Approval", domain=[('model_id', '=', _name)])
    
    def action_rfa(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        self._validate_dealer_sale_order()
        self.summary_discount_ids = False
        self._set_summary_discount()
        max_discount, product_id = self.get_approval_value()
        self.action_request_approval(value=max_discount, code='other', product_id=product_id)
        
    def action_approve(self):
        return super().action_approval()
        
    def action_reject(self):
        return super().action_reject_or_cancel(update_values={'state': 'draft'})
    
    def action_cancel_approval(self):
        return super().action_reject_or_cancel(update_values={'state': 'draft'})
    
    def get_approval_value(self):
        line_max_discount = max(self.summary_discount_ids, key=lambda disc: (disc.average_gross_profit, disc.id))
        return line_max_discount.average_gross_profit, line_max_discount.product_id.id
        
    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        res = super()._confirmation_error_message()
        if res == _("Some orders are not in a state requiring confirmation."):
            return False
        return res

    
