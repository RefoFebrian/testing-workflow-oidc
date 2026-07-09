# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class AccountMoveLineBankReconcile(models.Model):
    _inherit = "account.move.line"

    # 7: defaults methods

    # 8: fields
    reconciled_rk = fields.Boolean(string='Reconciled RK', default=False, copy=False)
    effective_date_reconcile = fields.Date(string='Effective Date Reconcile', copy=False)

    # 9: relation fields
    bank_reconcile_id = fields.Many2one(comodel_name='tw.bank.reconcile', string='Bank Reconcile', copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods

    # 14: private methods