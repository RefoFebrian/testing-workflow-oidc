# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_print_purchase_order(self):
        self.ensure_one()
        return self.env.ref('purchase.action_report_purchase_order').report_action(self)
