from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command


# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class InheritDealerSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    def _prepare_update_lot(self):
        self.ensure_one()
        vals = super()._prepare_update_lot()
        vals.update({
            'cdb_partner_id': self.order_id.cdb_stnk_id.id,
        })
        return vals
