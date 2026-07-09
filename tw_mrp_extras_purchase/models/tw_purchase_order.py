# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwMrpPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def button_confirm(self):
        self.validate_mandatory_extras()
        return super().button_confirm()

    # 13: action methods

    # 14: private methods
    def validate_mandatory_extras(self):
        for order in self:
            for line in order.order_line.filtered(lambda l: l.product_id):
                if line.product_id.categ_id.is_mandatory_extras:
                    bom = self.env['mrp.bom'].sudo()._bom_find(
                        line.product_id, company_id=order.company_id.id, bom_type='extras',
                    )[line.product_id]
                    if not bom:
                        raise ValidationError(_(
                            "Please configure EXTRAS for this product before confirming this Purchase Order.\n"
                            "Product '%s' belongs to category '%s' which requires Extras configuration. "
                        ) % (line.product_id.display_name, line.product_id.categ_id.name))