# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = 'Account Setting'

    journal_purchase_unit_id = fields.Many2one('account.journal', string='Journal Purchase Unit',help='Journal pembentukan invoice pembelian unit')
    journal_purchase_sparepart_id = fields.Many2one('account.journal', string='Journal Purchase Sparepart',help='Journal pembentukan invoice pembelian sparepart')
    journal_purchase_umum_id = fields.Many2one('account.journal', string='Journal Purchase Umum',help='Journal pembentukan invoice pembelian umum')
    account_purchase_discount_cash_id = fields.Many2one('account.account',string='Account Discount Cash Supplier')
    
    def _get_purchase_journal_id(self, company_id, division):
        journal = False
        branch_config_obj = self.env['tw.branch.setting'].suspend_security().search([('company_id','=',company_id)])
        if branch_config_obj:
            journal_id = False
            if division == 'Unit':
                journal_id = branch_config_obj.account_setting_id.journal_purchase_unit_id.id
            elif division == 'Sparepart':
                journal_id = branch_config_obj.account_setting_id.journal_purchase_sparepart_id.id
            elif division == 'Umum':
                journal_id = branch_config_obj.account_setting_id.journal_purchase_umum_id.id
            if journal_id:
                journal = journal_id
        return journal