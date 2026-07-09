# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockPickingBatchInherit(models.Model):
    _inherit = "stock.picking.batch"
    _description = "Stock Picking Batch"
    
    # 7: defaults methods

    # 8: fields
    amount_of_load = fields.Integer(related='stock_inbound_id.amount_of_load', string="Amount of Load")
    rope_condition = fields.Selection([
        ('good', 'Good'),
        ('not_good', 'Not Good'),
        ], string="Kondisi Tali Pengikatan", help="condition of the binding rope")
    sponge_count = fields.Integer(string="Total Spons", help="count of sponge")
    steel_count = fields.Integer(string="Total Besi", help="count of steel")
    saddle_count = fields.Integer(string="Total Pelana", help="count of saddle")

    # 9: relation fields
    stock_inbound_id = fields.Many2one(comodel_name='tw.stock.inbound', string="Stock Inbound")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('stock_inbound_id')
    def _onchange_stock_inbound_id(self):
        self.rope_condition = False
        self.sponge_count = False
        self.steel_count = False
        self.saddle_count = False
        if self.stock_inbound_id:
            self.rope_condition = self.stock_inbound_id.rope_condition
            self.sponge_count = self.stock_inbound_id.sponge_count
            self.steel_count = self.stock_inbound_id.steel_count
            self.saddle_count = self.stock_inbound_id.saddle_count

    # 12: override methods
    def action_confirm(self, auto_confirm=False):
        confirm = super(TwStockPickingBatchInherit, self).action_confirm(auto_confirm=auto_confirm)
        if not auto_confirm:
            self.picking_ids._add_qty_receipt()
        return confirm

    # 13: action methods

    # 14: private methods
    def _set_stock_inbound_id(self, picking):
        if self.stock_inbound_id or picking.stock_inbound_id:
            vals = {
                'stock_inbound_id': self.stock_inbound_id.id if self.stock_inbound_id else picking.stock_inbound_id.id,
            }
            if 'vehicle_id' in picking._fields:
                vals.update({
                    'vehicle_id': self.stock_inbound_id.vehicle_id.id if self.stock_inbound_id.vehicle_id else picking.stock_inbound_id.vehicle_id.id,
                })
            if 'driver_id' in picking._fields:
                vals.update({
                    'driver_id': self.stock_inbound_id.driver_id.id if self.stock_inbound_id.driver_id else picking.stock_inbound_id.driver_id.id,
                })
                
            picking.suspend_security().write(vals)

    # 15: action methods
    def action_done(self):
        self.ensure_one()
        res = super(TwStockPickingBatchInherit, self).action_done()
        if self.stock_inbound_id:
            self.stock_inbound_id.write({
                'rope_condition': self.rope_condition,
                'sponge_count': self.sponge_count,
                'steel_count': self.steel_count,
                'saddle_count': self.saddle_count,
            })

            self.move_line_ids.mapped('picking_id').write({
                'stock_inbound_id': self.stock_inbound_id.id
            })
        return res
