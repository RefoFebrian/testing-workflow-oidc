# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritTWStockPickingExtras(models.Model):
    _inherit = "stock.picking"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    extras_move_ids = fields.One2many('stock.move', 'picking_id', string="Extras Move", domain=[('division', '=', 'Extras')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_generate_extras(self):
        """Generate extras moves for the picking when it is in confirmed or assigned state.
        If extras already exist (incomplete or partial), they will be cancelled and deleted
        first, and then regenerated cleanly from scratch.
        """
        self.ensure_one()
        if self.backorder_id:
            raise Warning(_("This feature cannot be used on backorder documents."))
        if self.state not in ('confirmed', 'assigned'):
            raise Warning(_("Extras can only be generated when the picking is in Confirmed or Assigned state."))

        # Find unit moves that can generate BOM
        unit_moves = self.move_ids_without_extras.filtered(lambda m: m._is_generate_bom())
        if not unit_moves:
            raise Warning(_("No eligible unit moves found to generate extras."))

        # Cancel and delete existing active extras moves to ensure a clean regeneration
        active_extras = self.extras_move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
        if active_extras:
            active_extras._action_cancel()
            active_extras.unlink()

        # Regenerate extras moves cleanly from scratch
        existing_moves = self.move_ids
        exploded_moves = unit_moves.action_explode()
        new_moves = exploded_moves - existing_moves

        if new_moves:
            new_moves._action_confirm()
            if self.state == 'assigned':
                new_moves._action_assign()
        else:
            raise Warning(_("No extras moves were generated. Please check if the MRP BoM Extras is configured correctly for these products."))

    # 14: private methods
