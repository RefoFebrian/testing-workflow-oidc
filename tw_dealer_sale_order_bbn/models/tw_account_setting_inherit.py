# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    # 7: defaults methods
    def _get_domain_account_sales_bbn(self):
        branch_settings = self.env['tw.branch.setting'].search([('account_setting_id', '=', self.id)])
        if branch_settings:
            return [('company_id', 'parent_of', branch_settings.mapped('company_id').ids), ('account_type', '=', 'income')]

    def _get_domain_journal_purchase_bbn(self):
        branch_settings = self.env['tw.branch.setting'].search([('account_setting_id', '=', self.id)])
        if branch_settings:
            return [('company_id', 'parent_of', branch_settings.mapped('company_id').ids), ('type', '=', 'purchase')]

    # 8: fields
    is_accrue_proses_bbn = fields.Boolean(string='Accrue Proses BBN?', help="Check this if you want to accrue the BBN process for dealer sales orders")
    accrue_bbn_process = fields.Float(string='Amount Accure BBN', help="Amount of BBN process to be accrued",)

    # 9: relation fields
    account_dso_sales_bbn_id = fields.Many2one(
        comodel_name='account.account',
        string='Account Sales BBN',
        help="This account setting will be used as the account in the BBN sales invoice")

    journal_dso_purchase_bbn_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Purchase BBN',
        help="This journal setting will be used as the account in the BBN purchase invoice (accrue)")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods