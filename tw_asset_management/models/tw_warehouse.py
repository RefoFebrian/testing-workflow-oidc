# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


# TODO: ini jika ada kendala kalau menggunakan operation types pada incoming, tetapi jika tidak maka harus dihapus (SPJ)

class TwStockWarehouseAsset(models.Model):
    _inherit = "stock.warehouse"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    picking_type_asset_id = fields.Many2one('stock.picking.type', 'Picking Type Assets', check_company=True, copy=False)
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _get_picking_type_create_values(self, max_sequence):
        picking_type_create_values, max_sequence = super(TwStockWarehouseAsset, self)._get_picking_type_create_values(max_sequence)
        dest_location_asset = self.with_company(self.company_id)._get_or_create_asset_location()
        picking_type_create_values.update({
            'picking_type_asset_id': {
                'name': _('Receipts Assets'),
                'code': 'incoming',
                'use_existing_lots': False,
                'use_create_lots': False,
                'sequence': max_sequence + 1,
                'default_location_dest_id': dest_location_asset.id,
                'sequence_code': 'IN',
                'company_id': self.company_id.id,
                'division': 'Umum',
            }
        })
        return picking_type_create_values, max_sequence
    
    def _get_picking_type_update_values(self):
        input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)
        data = super(TwStockWarehouseAsset, self)._get_picking_type_update_values()
        dest_location_asset = self.with_company(self.company_id)._get_or_create_asset_location()
        data.update({
            'picking_type_asset_id': {
                'default_location_dest_id': dest_location_asset.id,
                'barcode': self.code.replace(" ", "").upper() + "IN-EXISTING-LOTS",
            }           
        })
        return data

    def _get_sequence_values(self, name=False, code=False):
        values = super(TwStockWarehouseAsset, self)._get_sequence_values(name=name, code=code) 
        values.update({
            'picking_type_asset_id': {
                'name': _('%(name)s Sequence in', name=name),
                'prefix': 'GR/' + str(self.company_id.code) + '/%(y)s/%(month)s/', 'padding': 5,
                'company_id': self.company_id.id,
            },
        })
        return values

    # 14: private methods
    def _get_or_create_asset_location(self):
        """
        Get existing 'Stock Assets' location or create one if not exists.
        Uses company_id, name, and type_id to ensure uniqueness.
        """
        self.ensure_one()
        
        # Search for existing Stock Assets location for this company
        type_id = self.env.ref('tw_asset_management.tw_select_stock_location_asset', raise_if_not_found=False)
        company = self.env.company
        parent_company = company.parent_id.id if company.parent_id else False
        dest_location_asset = self.env['stock.location'].search([
            ('name', '=', 'Stock Assets'),
            ('type_id', '=', type_id.id),
            ('company_id', 'in', [False, company.id, parent_company])
        ], limit=1)
        
        if not dest_location_asset:
            kwargs = {
                'type_id': type_id.id if type_id else False,
                'name': 'Stock Assets',
                'company_id': self.env.user.company_id.id
            }
            dest_location_asset = self.env['stock.location'].with_company(self.env.user.company_id)._create_location(**kwargs)
        
        return dest_location_asset
