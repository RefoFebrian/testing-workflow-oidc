# -*- coding: utf-8 -*-

from odoo import models, fields


class TwSaleOrderCancelBranchSetting(models.Model):
    """Inherit tw.branch.setting to add sale order cancel configuration."""
    _inherit = "tw.branch.setting"

    allow_cancel_so_with_payment = fields.Boolean(
        string='Allow Cancel SO with Payment',
        default=False,
        help='If checked, Sale Orders that already have payments can still be cancelled. '
             'If unchecked, Sale Orders with payments cannot be selected or confirmed for cancellation.',
    )
