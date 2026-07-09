# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TwWorkOrderInherit(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_auto_create_ar_payment_qris(self):
        self.ensure_one()
        if self.invoice_ids and self.invoice_count <= 1:
            return self.invoice_ids.action_auto_create_ar_payment_qris()
        
        raise Warning(f'Work Order {self.name} belum ada invoice yang dibuat!')