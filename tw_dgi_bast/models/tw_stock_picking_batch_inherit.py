# -*- coding: utf-8 -*-

# 3: imports of odoo
from odoo import models, fields


class StockPickingBatchInherit(models.Model):
    """
    Extend stock.picking.batch with DGI BAST fields.

    Fields added:
    - dgi_delivery_document_id → deliveryDocumentId dari DGI BAST
    - is_dgi → Flag indicating record was created from DGI sync
    - dgi_get_date → Timestamp when DGI data was fetched
    - dgi_get_uid → User who triggered the DGI sync
    """
    _inherit = "stock.picking.batch"

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    dgi_delivery_document_id = fields.Char(
        string="DGI Delivery Document ID",
        help="ID Surat Jalan dari DGI BAST API",
        copy=False,
        index=True,
    )
    is_dgi = fields.Boolean(
        string="From DGI",
        default=False,
        copy=False,
        help="Indicates this batch was created from DGI BAST sync",
    )
    dgi_get_date = fields.Datetime(
        string="DGI Sync Date",
        copy=False,
        help="Timestamp when DGI BAST data was fetched",
    )
    dgi_get_uid = fields.Many2one(
        "res.users",
        string="DGI Sync By",
        copy=False,
        help="User who triggered the DGI BAST sync",
    )

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------
    def action_open_dgi_bast_wizard(self):
        """Open DGI BAST sync wizard from Batch Out form/list button."""
        return {
            'name': 'Sync DGI BAST (Surat Jalan)',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.bast.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
