# -*- coding: utf-8 -*-

from odoo import models


class TwDealerSaleOrderCancelInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    def _get_additional_cancel_account_moves(self):
        """Hook for feature modules to expose extra moves tied to this DSO."""
        self.ensure_one()
        return self.env['account.move']

    def _get_additional_cancel_blocking_moves(self):
        """Hook for feature modules to expose extra moves that must block DSO cancellation."""
        self.ensure_one()
        return self.env['account.move']
