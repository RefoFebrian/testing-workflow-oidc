# -*- coding: utf-8 -*-

from odoo import models


class TwWorkOrderCancelInherit(models.Model):
    _inherit = "tw.work.order"

    def _get_additional_cancel_account_moves(self):
        """Hook for feature modules to expose extra moves that can be auto-reversed."""
        self.ensure_one()
        return self.env['account.move']

    def _get_additional_cancel_blocking_moves(self):
        """Hook for feature modules to expose extra moves that must block cancellation."""
        self.ensure_one()
        return self.env['account.move']
