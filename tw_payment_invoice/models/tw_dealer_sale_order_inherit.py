# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.fields import Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TwDealerSaleOrderInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_auto_create_ar_payment_va(self):
        self.ensure_one()
        # * case 1, cash and is_cod (true)
        if not self.finco_id and self.is_cod and self.state == 'sale':
            if not self.payment_ids and self.invoice_ids:
                inv_sl_obj = self.invoice_ids.filtered(lambda inv: 'SL' in inv.name)
                if inv_sl_obj:
                    inv_sl_obj.action_auto_create_ar_payment_va()

        # * case 2, credit and is_cod (true)
        elif self.finco_id and self.is_cod and self.state == 'sale':
            if not self.payment_ids and self.invoice_ids:
                inv_dp_obj = self.invoice_ids.filtered(lambda inv: 'DP' in inv.name)
                if inv_dp_obj:
                    inv_dp_obj.action_auto_create_ar_payment_va()
        else:
            raise Warning(f"Tidak bisa Auto Create Customer Payment (AR) atas DSO [{self.name}] ini!")