# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockWarehouseInherit(models.Model):
    _inherit = "stock.warehouse"

    purchase_return_type_id = fields.Many2one('stock.picking.type', 'Purchase Return Type')

    def _get_sequence_values(self):
        seq_vals = super(StockWarehouseInherit, self)._get_sequence_values()
        seq_vals.update({
            'purchase_return_type_id': {
                'name': self.name + ' Purchase Return',
                'prefix': self.code + '/RB/',
                'padding': 5,
                'company_id': self.company_id.id,
            },
        })
        return seq_vals

    def _get_picking_type_update_values(self):
        input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)
        res = super()._get_picking_type_update_values()
        res['purchase_return_type_id'] = {
            'default_location_src_id': input_loc.id,
            'default_location_dest_id': output_loc.id,
            'code': 'outgoing',
            'sequence': 6,
        }
        return res

    def _get_picking_type_create_values(self, max_sequence):
        picking_type_create_values, max_sequence  = super()._get_picking_type_create_values(max_sequence)

        return_vals = {
            'purchase_return_type_id': {
                'name': _('Purchase Returns'),
                'code': 'outgoing',
                'sequence': max_sequence + 1,
                'default_location_src_id': self.lot_stock_id.id,
                'default_location_dest_id': self.wh_output_stock_loc_id.id,
                'company_id': self.company_id.id,
                'sequence_code': 'OUT',
                'use_existing_lots': True,
                'use_create_lots': False,
            },
        }
        picking_type_create_values.update(return_vals)
        return picking_type_create_values, max_sequence
