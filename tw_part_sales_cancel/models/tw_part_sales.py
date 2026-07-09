# -*- coding: utf-8 -*-

from odoo import models


class TwPartSalesCancelInherit(models.Model):
    _inherit = "tw.part.sales"

    def _get_additional_cancel_account_moves(self):
        """Hook for feature modules to expose extra moves tied to this Part Sales."""
        self.ensure_one()
        return self.env['account.move']

    def _get_additional_cancel_blocking_moves(self):
        """Hook for feature modules to expose extra moves that must block Part Sales cancellation."""
        self.ensure_one()
        return self.env['account.move']
