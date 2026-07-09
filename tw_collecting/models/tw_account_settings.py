# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class TwAccountSetting(models.Model):
    """Extend account settings to include collecting configuration.
    
    This model adds collecting-specific settings to the base account settings.
    """
    _inherit = "tw.account.setting"
    _description = 'Account Setting'

    journal_collecting_id = fields.Many2one('account.journal', string='Journal Collecting AR/AP',help='Journal Collecting AR/AP')