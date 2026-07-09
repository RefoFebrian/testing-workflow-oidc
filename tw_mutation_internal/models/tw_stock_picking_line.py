# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class TWStockPickingLine(models.Model):
    _name = "tw.stock.picking.line"
    _description = "Stock Picking Line"
    
    # 8: fields
    quantity = fields.Float(string="Quantity", default=1)
    qty_available = fields.Float('Qty Available', digits='Product Unit of Measure', compute='_compute_qty_available', store=True)
    is_include_sublocations = fields.Boolean(string="Include Sublocations", related='picking_id.is_include_sublocations')
    
    # 9: relation fields
    picking_id = fields.Many2one(comodel_name='stock.picking', string="Picking")
    available_lot_ids = fields.Many2many(comodel_name='stock.lot', string="Available Serial Number", compute='_compute_available_lot_ids')
    available_location_ids = fields.Many2many(comodel_name='stock.location', string="Available Location", compute='_compute_available_location_ids')
    lot_id = fields.Many2one(comodel_name='stock.lot', string="Serial Number")
    location_id = fields.Many2one(comodel_name='stock.location', string="Location", compute='_compute_location_id', store=True)
    location_dest_id = fields.Many2one('stock.location', "Destination Location", compute="_compute_location_id", domain="[('usage', '=', 'internal')]", store=True, readonly=False, check_company=True)
    product_id = fields.Many2one(comodel_name='product.product', string="Product")
    tracking = fields.Selection(related='product_id.product_tmpl_id.tracking', readonly=True)
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('product_id','is_include_sublocations','location_id','picking_id.location_dest_id')
    def _compute_qty_available(self):
        for record in self:
            if record.product_id and record.location_id:
                record._renew_availability()
            else:
                record.qty_available = 0
    
    @api.depends('picking_id.location_id','lot_id')
    def _compute_location_id(self):
        for record in self:
            record.location_dest_id = record.picking_id.location_dest_id
            if record.lot_id:
                record.location_id = record.lot_id.location_id
            else:
                record.location_id = record.picking_id.location_id
    
    @api.depends('product_id','picking_id.location_id','is_include_sublocations','picking_id.location_dest_id')
    def _compute_available_lot_ids(self):
        for record in self:
            if record.product_id:
                lot_ids = self.env['stock.quant'].get_available_lot_stock(record.product_id.id, record.picking_id.company_id.id, record.picking_id.location_id.id, record.is_include_sublocations, location_dest_id=record.picking_id.location_dest_id.id)
                record.available_lot_ids = [(6, 0, lot_ids.ids)]
            else:
                record.available_lot_ids = False
    
    @api.depends('product_id','picking_id.location_id','is_include_sublocations','picking_id.location_dest_id')
    def _compute_available_location_ids(self):
        for record in self:
            if record.product_id and record.picking_id.location_id:
                if record.is_include_sublocations:
                    location_ids = self.env['stock.quant'].with_company(record.picking_id.company_id).sudo()._get_location_available_by_product(record.product_id, record.picking_id.company_id.id, record.picking_id.location_id.id)
                    record.available_location_ids = [(6, 0, location_ids)]
                else:
                    record.available_location_ids = [(6, 0, [record.picking_id.location_id.id])]
            else:
                record.available_location_ids = False
    
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for record in self:
            if record.lot_id:
                record.product_id = record.lot_id.product_id
    
    @api.onchange('quantity')
    def _onchange_quantity(self):
        for record in self:
            if record.quantity <= 0:
                return {
                    'value': {
                        'quantity': 1,
                    },
                    'warning': {
                        'title': _("Warning"),
                        'message': _("Quantity must be greater than 0"),
                    }
                }

            if record.picking_id.division == 'Unit' and record.quantity > 1:
                return {
                    'value': {
                        'quantity': 1,
                    },
                    'warning': {
                        'title': _("Warning"),
                        'message': _("Quantity must be 1 for Internal Transfer Unit"),
                    }
                }

    # 12: override methods
    
    # 13: action methods

    # 14: private methods
    def _renew_availability(self):
        for record in self:
            record.qty_available = self.env['stock.quant'].get_stock_available(record.product_id.id, record.picking_id.company_id.id, False, record.location_id.id, location_dest_id=record.picking_id.location_dest_id.id)
    

