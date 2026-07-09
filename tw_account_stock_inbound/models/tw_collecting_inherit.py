# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwCollectingInherit(models.Model):
    """Extend tw.collecting with stock inbound relation for expedition accrue."""

    _inherit = "tw.collecting"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    stock_inbound_id = fields.Many2one(
        comodel_name='tw.stock.inbound',
        string='Stock Inbound',
        ondelete='restrict',
        help='Related stock inbound for expedition accrue'
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('stock_inbound_id')
    def _onchange_stock_inbound_id(self):
        """Auto-populate partner from expedition on stock inbound."""
        if self.stock_inbound_id and self.stock_inbound_id.expedition_id:
            self.partner_id = self.stock_inbound_id.expedition_id.id

    # 12: override methods

    # 13: action methods

    # 14: private methods
