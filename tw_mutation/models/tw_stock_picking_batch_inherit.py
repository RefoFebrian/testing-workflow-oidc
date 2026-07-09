# -*- coding: utf-8 -*-

# 3: imports of odoo
from odoo import models


class StockPickingBatchMutation(models.Model):
    """Extend stock.picking.batch to handle lot company update for mutation transfers.

    Odoo's native batch action_done validates all pickings together, which may
    bypass individual picking button_validate overrides. This ensure lot.company_id
    is updated to the receiver company BEFORE check_quantity() runs, preventing
    the 'The serial number has already been assigned' validation error.
    """
    _inherit = "stock.picking.batch"

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------
    def action_done(self):
        """Override to update lot company for incoming mutation pickings before validation.

        Must run before super() so that check_quantity() (triggered inside
        Odoo's native action_done) sees the serial number already belonging
        to the receiving company, not the sending company.
        """
        incoming_mutation_pickings = self.picking_ids.filtered(
            lambda p: p.sudo().mutation_order_id
            and p.picking_type_id.code == 'incoming'
            and p.state not in ('done', 'cancel')
        )
        if incoming_mutation_pickings:
            incoming_mutation_pickings.sudo()._update_destination_company_lot_ids()
        return super().action_done()
