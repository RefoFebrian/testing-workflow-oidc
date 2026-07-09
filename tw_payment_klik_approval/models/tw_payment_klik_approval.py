# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritApproval(models.Model):
    _inherit = "tw.approval"

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods

    def update_record_with_value_from_context(self, trx, context):
        if trx and hasattr(trx, 'is_payment_klik') and trx.is_payment_klik:
            vals = {
                'is_payment_klik': False,
                'payment_klik_uid': False,
                'payment_klik_date': False
            }
            mutable_context = dict(context)
            update_value = mutable_context.get('update_value', False)
            if update_value:
                mutable_context['update_value'] = vals | update_value
            else:
                mutable_context['update_value'] = vals
            context = mutable_context
            
        return super().update_record_with_value_from_context(trx, context)