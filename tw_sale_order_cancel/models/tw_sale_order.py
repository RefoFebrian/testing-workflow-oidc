# -*- coding: utf-8 -*-

from odoo import models


class TwSaleOrderCancelInherit(models.Model):
    _inherit = "tw.sale.order"

    def _get_additional_cancel_account_moves(self):
        """Hook for feature modules to expose extra moves tied to this SO."""
        self.ensure_one()
        return self.env['account.move']

    def _get_additional_cancel_blocking_moves(self):
        """Hook for feature modules to expose extra moves that must block SO cancellation."""
        self.ensure_one()
        return self.env['account.move']
