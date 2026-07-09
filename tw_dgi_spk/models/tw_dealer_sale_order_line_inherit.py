# -*- coding: utf-8 -*-

from odoo import models


class TwDealerSaleOrderLineInherit(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    def _prepare_update_lot(self):
        self.ensure_one()
        vals = super()._prepare_update_lot()
        if self.order_id.spk_id and self.order_id.spk_id.source_document and self.order_id.spk_id.is_dgi:
            vals["dgi_spk_number"] = self.order_id.spk_id.source_document
        return vals
