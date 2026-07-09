# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.sql import column_exists, create_column

# 5: local imports

# 6: Import of unknown third party lib

class DealerSaleOrderStockLot(models.Model):
    _inherit = "stock.lot"

    sale_order_count = fields.Integer('Sale order count', compute='_compute_dealer_sale_order_id')
    downpayment = fields.Float('Uang Muka')

    do_date = fields.Date(string="DO Date")
    invoice_date = fields.Date(string="Invoice Date")
    
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', tracking=True)
    dealer_sale_order_id = fields.Many2one('tw.dealer.sale.order', string="Dealer Sales Order")    
    sales_order_reserved_id = fields.Many2one('tw.dealer.sale.order', string="Sales Order Reserved")
    customer_reserved_id = fields.Many2one('res.partner', string="Customer Reserved")
    payment_type_id = fields.Many2one('tw.selection', string='Tipe Pembayaran', domain=[('type','=','PaymentType')])

    @api.depends('name')
    def _compute_dealer_sale_order_id(self):
        sale_orders = defaultdict(lambda: self.env['tw.dealer.sale.order'])
        for move_line in self.env['stock.move.line'].search([('lot_id', 'in', self.ids), ('state', '=', 'done')]):
            move = move_line.move_id
            if move.picking_id.location_dest_id.usage in ('customer', 'transit') and move.dealer_sale_order_line_id.order_id:
                sale_orders[move_line.lot_id.id] |= move.dealer_sale_order_line_id.order_id
        for lot in self:
            lot.sale_order_count = len(lot.dealer_sale_order_id)

    def action_view_so(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['domain'] = [('id', 'in', self.mapped('dealer_sale_order_id.id'))]
        action['context'] = dict(self._context, create=False)
        return action