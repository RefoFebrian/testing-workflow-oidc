# -*- coding: utf-8 -*-

from odoo import fields, models


class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    hutang_lain_account_line_id = fields.Many2one(
        'account.account',
        'Account Line Hutang Lain',
        domain=[('account_type', '=', 'liability_payable')],
        help="Field ini digunakan untuk setting account. pada transaksi Hutang Lain Line",
    )
