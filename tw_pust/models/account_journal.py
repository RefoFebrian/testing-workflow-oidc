# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import fields, models, api

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class AccountJournalPust(models.Model):
    """Extends account.journal to support PUST (Cash-in-Transit).

    Adds:
    - 'Transit' journal type for Money-In-Transit (MN01xxx) journals.
    - 'is_pusted' flag to track whether a cash journal has been deposited
      to transit. Used by tw_payment to filter available payment journals.
    - action_check_pust() to verify and reset is_pusted based on balance.
    """
    _inherit = "account.journal"
    
    # 7: defaults methods

    # 8: fields
    type = fields.Selection(
        selection_add=[
            ('transit', 'Transit')
        ],
        ondelete={'transit': 'set general'},
    )
    is_pusted = fields.Boolean(
        string="Sudah PUST?",
        default=True,
        help="Indicates this cash journal has been deposited to a transit "
             "account. Default True; reset by action_check_pust when "
             "cash balance is not zero.",
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods 
    def action_check_pust(self):
        """Check all cash journals and reset is_pusted based on balance.

        Iterates through all cash journals where is_pusted=True.
        For each, calculates the actual balance of the default debit account.
        If balance != 0, sets is_pusted = False (meaning cash has not been
        fully deposited to transit yet).

        Replicates wtc_bank_transfer/wtc_account_journal.py action_check_pust.
        Can be called as a scheduled action (cron) or manually.
        """
        journals = self.search([
            ('type', '=', 'cash'),
            ('is_pusted', '=', True),
        ])

        for journal in journals:
            if not journal.default_debit_account_id:
                continue

            # Calculate balance using raw SQL for performance
            # (replicates teds approach)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(debit) - SUM(credit), 0.0) AS balance
                FROM account_move_line
                WHERE account_id = %s
                  AND parent_state = 'posted'
            """, (journal.default_debit_account_id.id,))

            result = self.env.cr.dictfetchone()
            balance = result.get('balance', 0.0) if result else 0.0

            if round(balance, 2) != 0:
                journal.write({'is_pusted': False})
    
    # 14: private methods
