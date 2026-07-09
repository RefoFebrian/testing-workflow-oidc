# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderLine(models.Model):
    _inherit = "tw.work.order.line"

    # 7: defaults methods

    # 8: fields
    warranty = fields.Float(string='Warranty', default=0.0, help="Warranty in days, (i.e. 2.5 = 2.5 Days)")

    # Selection

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('product_id')
    def _onchange_warranty(self):
        self.warranty = 0
        if self.product_id:
            self.warranty = self.product_id.product_tmpl_id.categ_id.warranty

    # 12: override methods