# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWConfirmationPaymentActivityWizard(models.TransientModel):
    _name = "tw.payment.activity.wizard"
    _description = "Confirmation Payment Activity Wizard"

    payment_choice = fields.Selection([
        ('bs', 'BS (Advance Payment)'),
        ('nc', 'NC (Payment Request)'),
    ], string='Skema Pembayaran')

    lpj_id = fields.Many2one('tw.activity.atl.btl.line', string='LPJ')

    def action_confirm_payment_choice(self):
        if self.payment_choice == 'bs':
            self.lpj_id.action_create_advance_payment()
        elif self.payment_choice == 'nc':
            self.lpj_id.action_create_payment_request()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }