# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwCollectingExpeditionLine(models.Model):
    """Detail lines for Collecting Expedition.

    Stores breakdown per stock move line: picking number, product, no mesin
    (lot), no rangka (chassis number, if unit/serial_chassis tracking), and qty.
    Auto-populated from stock_inbound_ids on the parent record.
    """

    _name = "tw.collecting.expedition.line"
    _description = "Collecting Expedition Line"
    _order = "collecting_expedition_id, picking_id, id"

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    qty = fields.Float(
        string="Qty",
        digits=(16, 2),
    )
    chassis_number = fields.Char(
        string="No Rangka",
        help="Nomor Rangka kendaraan (hanya untuk divisi Unit dengan tracking serial_chassis)",
        readonly=True,
    )

    # -------------------------------------------------------------------------
    # RELATION FIELDS
    # -------------------------------------------------------------------------
    collecting_expedition_id = fields.Many2one(
        comodel_name="tw.collecting.expedition",
        string="Collecting Expedition",
        required=True,
        ondelete="cascade",
        index=True,
    )
    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="No Picking",
        readonly=True,
        ondelete="restrict",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        readonly=True,
        ondelete="restrict",
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot / No Mesin",
        readonly=True,
        ondelete="restrict",
    )
