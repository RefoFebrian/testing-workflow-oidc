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

class TWStockPickingLineInherit(models.Model):
    _inherit = "tw.stock.picking.line"
    
    # 8: fields
    is_rfs = fields.Boolean(string='RFS', default=True)
    available_location_dest_ids = fields.Many2many(comodel_name='stock.location', string="Available Destination Location", compute='_compute_available_location_dest_ids')
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('is_rfs')
    def _onchange_is_rfs(self):
        self.location_dest_id = False

    @api.depends('product_id', 'location_dest_id', 'picking_id.location_dest_id')
    def _compute_available_location_dest_ids(self):
        for record in self:
            type_domain_search = ['|', ('type_id.value', '!=', 'nrfs'), ('type_id', '=', False)]
            if not record.is_rfs:
                type_domain_search = [('type_id.value', '=', 'nrfs')]
            type_domain_search.append(('id', 'child_of', record.picking_id.location_dest_id.id))
            type_domain_search.append(('usage', 'not in', ('customer', 'supplier', 'view')))

            record.available_location_dest_ids = [(6, 0, self.env['stock.location'].search(type_domain_search).ids)]

    @api.depends('picking_id.location_id','lot_id','available_location_dest_ids','picking_id.location_dest_id')
    def _compute_location_id(self):
        super()._compute_location_id()
        for record in self:
            if record.location_dest_id.id not in record.available_location_dest_ids.ids:
                record.location_dest_id = False
            
            is_child = record.location_dest_id.id in self.env['stock.location'].search([
                ('id', '=', record.location_dest_id.id),
                ('id', 'child_of', record.picking_id.location_dest_id.id)
            ]).ids
            if not is_child:
                record.location_dest_id = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for line in res:
            if line.location_dest_id:
                line._check_line_nrfs()
        return res

    def write(self, vals):
        res = super().write(vals)
        for line in self:
            if line.location_dest_id:
                line._check_line_nrfs()
        return res
    
    # 13: action methods

    # 14: private methods
    def _check_line_nrfs(self):
        self.ensure_one()
        if not self.is_rfs and self.location_dest_id.type_id.value != 'nrfs':
            raise Warning("Terdapat product yang NRFS, Destination Location harus NRFS!")
        return True
