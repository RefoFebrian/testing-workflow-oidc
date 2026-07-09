# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, SUPERUSER_ID, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwBank(models.Model):
    _name = "res.bank"
    _inherit = ["res.bank", "mail.thread"]
    _rec_names_search = ['name', 'code']

    code = fields.Char('Code', tracking=True ,help='EX: BCA')
    transfer_code = fields.Char('3 Digit Code', help='Code for transfer money between different Bank. EX : 014', tracking=True)
    
    is_restrict_length = fields.Boolean('Restrict length?', help='Restrict length of account number ex : 10 for BCA', tracking=True)
    allowed_length = fields.Integer('Allowed Length', help='Allowed Length of account number ex : 10 for BCA', tracking=True)

    @api.depends('name','code')
    def _compute_display_name(self):
        for bank in self:
            name = (bank.name or '') + (bank.code and (' - ' + bank.code) or '')
            bank.display_name = name

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(TwBank, self).create(vals_list)
        create.validity_check()
        return create

    def write(self, vals):
        write = super(TwBank, self).write(vals)
        self.validity_check()
        return write
    
    @api.model
    def _search_display_name(self, operator, value):
        if operator in ('ilike', 'not ilike') and value:
            domain = ['|', ('code', '=ilike', value + '%'), ('name', 'ilike', value)]
            if operator == 'not ilike':
                domain = ['!', *domain]
            return domain
        return super()._search_display_name(operator, value)


    # 13: action methods

    # 14: private methods
    def validity_check(self):
        for rec in self:
            if rec.is_restrict_length and rec.allowed_length <= 0:
                raise Warning(f"Allowed Length must be greater than 0")
                