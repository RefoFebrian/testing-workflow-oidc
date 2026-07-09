# -*- coding: utf-8 -*-

from odoo import models, fields

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    journal_disposal_asset_hl_id = fields.Many2one('account.journal', string='Journal Hutang Lain Reconcile', help='Journal Hutang Lain Reconcile')
