# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _


class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    # 7: defaults methods
    def _get_domain_journal_downpayment(self):
        branch_settings = self.env['tw.branch.setting'].search([('account_setting_id', '=', self.id)])
        if branch_settings:
            return [('company_id', 'parent_of', branch_settings.mapped('company_id').ids), ('type', '=', 'sale')]

    def _get_domain_journal_downpayment_allocation(self):
        branch_settings = self.env['tw.branch.setting'].search([('account_setting_id', '=', self.id)])
        if branch_settings:
            return [('company_id', 'parent_of', branch_settings.mapped('company_id').ids), ('type', '=', 'general')]

    # 8: fields
    
    # 9: relation fields
    journal_dso_settlement_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Pelunasan SO',
        help="Journal ini digunakan untuk membuat invoice pelunasan")
    
    journal_dso_downpayment_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Downpayment',
        domain=_get_domain_journal_downpayment,
        help="Account credit di journal ini digunakan memotong invoice pelunasan jika ada DP")

    journal_dso_downpayment_allocation_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Alokasi DP',
        domain=_get_domain_journal_downpayment_allocation,
        help="Journal ini digunakan untuk membuat invoice alokasi DP.")
    
    # Discount
    account_dso_discount_regular_id = fields.Many2one(
        comodel_name='account.account',
        string='Account Discount Regular',
        help="Account ini digunakan untuk membuat invoice line discount regular")
