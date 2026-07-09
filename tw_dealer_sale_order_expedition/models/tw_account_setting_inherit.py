# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    # 7: defaults methods

    # 8: fields
    is_accrue_expedition = fields.Boolean(string='Accrue Expedition?', help="Check this if you want to accrue the expedition process for dealer sales orders")
    accrue_expedition = fields.Float(string='Amount Accure Expedition', help="Amount of expedition process to be accrued",)

    # 9: relation fields
    journal_dso_accrue_ekspedisi_id = fields.Many2one('account.journal','Journal Accrue Dana Ongkos Angkut')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('is_accrue_expedition')
    def _onchange_is_accrue_expedition(self):
        if not self.is_accrue_expedition:
            self.accrue_expedition = 0

    # 12: override methods

    # 13: action methods