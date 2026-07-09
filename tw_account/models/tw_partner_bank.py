# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from validate_email import validate_email

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessError

# 5: local imports

# 6: Import of unknown third party lib

class TwResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    # 7: defaults methods

    # 8: fields
    code = fields.Char('Code')
    allow_out_payment = fields.Boolean('Allow Send Money?', help='This account can be used for outgoing payments', default=True, copy=False, readonly=False)
    
    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(TwResPartnerBank, self).create(vals_list)
        create.validity_check()
        return create

    def write(self, vals):
        write = super(TwResPartnerBank, self).write(vals)
        self.validity_check()
        return write

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_partner.group_tw_partner_bank_account_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    # 13: action methods

    # 14: private methods
    def validity_check(self):
        for rec in self:
            if rec.active:
                if rec.acc_number and rec.bank_id.is_restrict_length and len(rec.acc_number) != rec.bank_id.allowed_length:
                    raise Warning(f"Account Number {rec.acc_number} must have {rec.bank_id.allowed_length} characters")
                