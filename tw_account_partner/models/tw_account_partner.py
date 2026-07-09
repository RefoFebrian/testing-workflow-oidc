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


class TwAccountPartner(models.Model):
    _inherit = "res.partner"
    _description = 'Partner Account Setting'
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    property_account_payable_id = fields.Many2one(
        'account.account',
        string="Account Payable",
        domain="[('account_type', '=', 'liability_payable')]",
        help="This account will be used instead of the default one as the payable account for the current partner")
    
    property_account_receivable_id = fields.Many2one(
        'account.account',
        string="Account Receivable",
        domain="[('account_type', '=', 'asset_receivable')]",
        help="This account will be used instead of the default one as the receivable account for the current partner")
    