from collections import defaultdict

import markupsafe

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import frozendict, SQL


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        
        context = self.env.context
        model = context.get('active_model')
        ids = context.get('active_ids')
    
        invoice = self.env[model].browse(ids).move_id
        
        source = invoice.line_ids.filtered(lambda x: x.purchase_line_id).purchase_line_id.order_id
        payment_vals['company_id'] = self.env.user.company_id.id
        payment_vals['beneficiary_company_id'] = source.company_id.id
        payment_vals['division'] = source.division
                
        return payment_vals

