# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, api

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class TwAccountPaymentPust(models.Model):
    """Extends tw.account.payment to filter journals by PUST status.

    In teds (Odoo 8), wtc_account_voucher.onchange_branch filters journals with:
        domain['journal_id'] = [
            ('branch_id','=',branch),
            ('type','in',['bank','cash','edc']),
            ('is_pusted','=',True)
        ]

    This ensures users can only create payments from journals that
    have been properly PUST-ed (cash deposited to transit).

    This module replicates that logic by extending the available
    journal computation in tw.account.payment.
    """
    _inherit = "tw.account.payment"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & onchange methods
    @api.depends('payment_type', 'company_id')
    def _compute_available_journal_ids(self):
        """Override to filter out non-PUST journals.

        After computing the base available journals, further filter
        to only include journals where is_pusted=True. This prevents
        users from making payments from cash journals that haven't
        been deposited to transit.
        """
        super()._compute_available_journal_ids()

        for pay in self:
            if pay.available_journal_ids:
                pay.available_journal_ids = pay.available_journal_ids.filtered(
                    lambda j: j.is_pusted
                )
    # 12: override methods

    # 13: action methods

    # 14: private methods

