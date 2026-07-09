# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    interbranch_in_type_id = fields.Many2one('stock.picking.type', 'Interbranch In Type', check_company=True, copy=False)
    interbranch_out_type_id = fields.Many2one('stock.picking.type', 'Interbranch Out Type', check_company=True, copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _get_picking_type_create_values(self, max_sequence):
        """Override to add interbranch picking type values."""
        picking_type_create_values, max_sequence = super()._get_picking_type_create_values(max_sequence)
        
        # Get transit location
        transit_location = self._get_transit_location()
        stock_location = self.lot_stock_id

        # Interbranch In: Source = Supplier, Dest = Stock
        picking_type_create_values.update({
            'interbranch_in_type_id': {
                'name': _('Interbranch In'),
                'code': 'incoming',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 1,
                'default_location_src_id': transit_location.id,
                'default_location_dest_id': stock_location.id,
                'sequence_code': 'WHI',
                'company_id': self.company_id.id,
            },
            'interbranch_out_type_id': {
                'name': _('Interbranch Out'),
                'code': 'outgoing',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 2,
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': transit_location.id,
                'sequence_code': 'WHO',
                'company_id': self.company_id.id,
            }
        })
        return picking_type_create_values, max_sequence + 2

    def _get_picking_type_update_values(self):
        """Override to update interbranch picking type values."""
        data = super()._get_picking_type_update_values()
        
        transit_location = self._get_transit_location()
        stock_location = self.lot_stock_id

        data.update({
            'interbranch_in_type_id': {
                'default_location_src_id': transit_location.id,
                'default_location_dest_id': stock_location.id,
                'barcode': self.code.replace(" ", "").upper() + "-IBIN",
            },
            'interbranch_out_type_id': {
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': transit_location.id,
                'barcode': self.code.replace(" ", "").upper() + "-IBOUT",
            }
        })
        return data

    def _get_sequence_values(self):
        """Override to add interbranch sequence values."""
        values = super()._get_sequence_values()
        values.update({
            'interbranch_in_type_id': {
                'name': self.name + ' Interbranch In',
                'prefix': 'WH/' + 'IN/' + str(self.company_id.code) + '/%(y)s/%(month)s/',
                'padding': 5,
                'company_id': self.company_id.id,
            },
            'interbranch_out_type_id': {
                'name': self.name + ' Interbranch Out',
                'prefix': 'WH/' + 'OUT/' + str(self.company_id.code) + '/%(y)s/%(month)s/',
                'padding': 5,
                'company_id': self.company_id.id,
            },
        })
        return values

    # 14: private methods
    def _get_transit_location(self):
        """Get transit location for interbranch transfers.
        
        Prioritize transit location without company_id (intercompany transit)
        because Odoo considers transit with company_id as 'valued' location.
        When destination is 'valued', the move is NOT classified as 'out',
        which prevents journal entry creation on WH/OUT.
        
        Returns:
            recordset: Transit location for interbranch use
        """
        # Prioritas: transit tanpa company_id (intercompany transit)
        # agar Odoo mengklasifikasikan move sebagai OUT dan membuat journal entry
        transit_location = self.env['stock.location'].search([
            ('usage', '=', 'transit'),
            ('company_id', '=', False),
        ], limit=1)

        if not transit_location:
            # Fallback: transit dengan company_id yang sama
            transit_location = self.env['stock.location'].search([
                ('usage', '=', 'transit'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)

        return transit_location
