# -*- coding: utf-8 -*-

from odoo import models, fields


class TwAccountSettingExpedition(models.Model):
    """Extend account setting with expedition collecting journal config."""
    _inherit = "tw.account.setting"

    journal_collecting_expedition_id = fields.Many2one(
        'account.journal',
        string='Journal Collecting Expedition',
        help='Journal for Collecting Expedition entries'
    )
