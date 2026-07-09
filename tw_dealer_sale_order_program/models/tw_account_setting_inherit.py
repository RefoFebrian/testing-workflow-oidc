# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    #7 defaults methods
    def _get_domain_journal_subsidy_md(self):
        branch_settings = self.env['tw.branch.setting'].search([('account_setting_id', '=', self.id)])
        if branch_settings:
            return [('company_id', 'parent_of', branch_settings.mapped('company_id').ids), ('type', '=', 'sale')]

    def _get_domain_journal_subsidy_finco(self):
        branch_settings = self.env['tw.branch.setting'].search([('account_setting_id', '=', self.id)])
        if branch_settings:
            return [('company_id', 'parent_of', branch_settings.mapped('company_id').ids), ('type', '=', 'sale')]

    #8 fields

    #9 related fields
    account_dso_discount_quotation_id = fields.Many2one(
        comodel_name='account.account',
        string='Account Discount Quotation',
        help="This account will be used for the account in the quotation discount invoice. formerly known as dealer_so_account_potongan_subsidi_id")
    
    account_dso_remaining_subsidy_id = fields.Many2one(
        comodel_name='account.account',
        string='Account Sisa Program Subsidi',
        help="This account will be used for tracking the remaining subsidy. formerly known as dealer_so_account_sisa_subsidi_id")

    journal_dso_subsidy_finco_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Subsidi Finco',
        domain=_get_domain_journal_subsidy_finco,
        help="This journal will be used for recording subsidy transactions from Finco. formerly known as dealer_so_journal_psfinco_id")

    journal_dso_subsidy_md_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Subsidi MD',
        domain=_get_domain_journal_subsidy_md,
        help="This journal will be used for recording subsidy transactions from MD. formerly known as dealer_so_journal_psmd_id")