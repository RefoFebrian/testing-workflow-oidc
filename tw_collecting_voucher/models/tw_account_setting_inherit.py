# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountSettingCollectingVoucher(models.Model):
    _inherit = "tw.account.setting"

    # 7: defaults methods

    # 8: fields
    
    # 9: relation fields
    journal_collecting_voucher_id = fields.Many2one('account.journal', 'Journal Collecting Voucher', help='Select a Journal for Collecting Voucher')
    account_collecting_remaining_voucher_id = fields.Many2one('account.account', 'Account Collecting Sisa Voucher', help='Select a Account Collecting Remaining Voucher')
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods