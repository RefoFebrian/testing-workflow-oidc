# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class AccountPaymentInherit(models.Model):
    _inherit = "tw.account.payment"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_approval(self):
        self.ensure_one()
        approval = super().action_approval()
        check_state = self.state == 'approved' and self.approval_state == 'approved'
        if check_state and self.payment_method_line_id.payment_provider_id.code == 'astrapay':
            self.state = 'in_process'

        return approval

    # 14: private methods
    def _get_domain_account_payment_method(self):
        domain = super()._get_domain_account_payment_method()
        if not any(cond[0] == 'code' for cond in domain):
            domain.append(('code', 'not in', ['astrapay']))
        else:
            for cond in domain:
                if cond[0] == 'code':
                    cond[2].append('astrapay')
                    break
        
        return domain