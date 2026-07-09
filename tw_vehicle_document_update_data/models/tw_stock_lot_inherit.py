# -*- coding: utf-8 -*-

from odoo import models, fields


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    change_lot_ids = fields.One2many("tw.vehicle.document.update.data", "lot_id",string = "Detail Pengubahan Kata")

