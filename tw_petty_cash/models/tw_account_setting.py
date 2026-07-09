# -*- coding: utf-8 -*-

from odoo import fields, models


class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    pettycash_journal_id = fields.Many2one(
        'account.journal',
        string='Payment Method Petty Cash',
        help='Payment Method Untuk Patty Cash',
        domain="[('type', '=', 'petty_cash')]",
    )
