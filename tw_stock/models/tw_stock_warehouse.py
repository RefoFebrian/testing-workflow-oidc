# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwStockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    in_type_existing_lots_id = fields.Many2one('stock.picking.type', 'Picking Type with use Existing Lots', check_company=True, copy=False)
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _get_company_warehouse(self,company_id):
        warehouse = company_id.warehouse_id
        if not warehouse:
            warehouse = self.search([('company_id', '=', company_id.id)], limit=1)
        return warehouse
        
    def _get_picking_type_create_values(self, max_sequence):
        picking_type_create_values, max_sequence = super(TwStockWarehouse, self)._get_picking_type_create_values(max_sequence)
        picking_type_create_values.update({
            'in_type_existing_lots_id': {
                'name': _('Receipts'),
                'code': 'incoming',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 1,
                'sequence_code': 'IN',
                'company_id': self.company_id.id,
            }
        })
        return picking_type_create_values, max_sequence
    
    def _get_picking_type_update_values(self):
        input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)
        data = super(TwStockWarehouse, self)._get_picking_type_update_values()
        data.update({
            'in_type_existing_lots_id': {
                'default_location_dest_id': input_loc.id,
                'barcode': self.code.replace(" ", "").upper() + "IN-EXISTING-LOTS",
            }           
        })
        return data

    def _get_sequence_values(self, name=False, code=False):
        values = super(TwStockWarehouse, self)._get_sequence_values(name=name, code=code)
        values.get('in_type_id', False).update({
            'name': 'Receipts Sequence IN',
            'prefix': 'WH/' + 'IN/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
        values.get('out_type_id', False).update({
            'name': 'Delivery Sequence OUT',
            'prefix': 'WH/' + 'OUT/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
        values.get('pack_type_id', False).update({
            'name': 'Packing Sequence PACK',
            'prefix': 'WH/' + 'PACK/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
        values.get('pick_type_id', False).update({
            'name': 'Picking Sequence PICK',
            'prefix': 'WH/' + 'PICK/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
        values.get('qc_type_id', False).update({
            'name': 'QC Sequence Quality Control',
            'prefix': 'WH/' + 'QC/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
        values.get('store_type_id', False).update({
            'name': 'Store Sequence STOR',
            'prefix': 'WH/' + 'STOR/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
        values.get('int_type_id', False).update({
            'name': 'Internal Sequence INT',
            'prefix': 'MU/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
            'company_id': self.company_id.id,
        })
      
        values.update({
            'in_type_existing_lots_id': {
                'name': 'Receipts Sequence IN Existing',
                'prefix': 'WH/' + 'IN/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
                'company_id': self.company_id.id,
            },
        })
        return values

