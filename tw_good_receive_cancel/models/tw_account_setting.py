# -*- coding: utf-8 -*-

from odoo import models, fields


class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    journal_good_receive_cancel_id = fields.Many2one(
        'account.journal',
        string='Journal Good Receive Cancel',
        help="Journal untuk membalik Journal Good Receive saat cancel"
    )
