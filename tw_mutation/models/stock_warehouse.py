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
    interbranch_in_unit_type_id = fields.Many2one(
        'stock.picking.type', 'Interbranch In Type (Unit)',
        check_company=True, copy=False)
    interbranch_out_unit_type_id = fields.Many2one(
        'stock.picking.type', 'Interbranch Out Type (Unit)',
        check_company=True, copy=False)
    interbranch_in_sparepart_type_id = fields.Many2one(
        'stock.picking.type', 'Interbranch In Type (Sparepart)',
        check_company=True, copy=False)
    interbranch_out_sparepart_type_id = fields.Many2one(
        'stock.picking.type', 'Interbranch Out Type (Sparepart)',
        check_company=True, copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _get_picking_type_create_values(self, max_sequence):
        """Override to add interbranch picking type values for Unit and Sparepart divisions."""
        picking_type_create_values, max_sequence = super()._get_picking_type_create_values(max_sequence)
        
        # Get transit location
        transit_location = self._get_transit_location()
        stock_location = self.lot_stock_id

        # Unit Division
        picking_type_create_values.update({
            'interbranch_in_unit_type_id': {
                'name': _('Interbranch In (Unit)'),
                'code': 'incoming',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 1,
                'default_location_src_id': transit_location.id,
                'default_location_dest_id': stock_location.id,
                'sequence_code': 'WHI',
                'company_id': self.company_id.id,
            },
            'interbranch_out_unit_type_id': {
                'name': _('Interbranch Out (Unit)'),
                'code': 'outgoing',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 2,
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': transit_location.id,
                'sequence_code': 'WHO',
                'company_id': self.company_id.id,
            },
            # Sparepart Division
            'interbranch_in_sparepart_type_id': {
                'name': _('Interbranch In (Sparepart)'),
                'code': 'incoming',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 3,
                'default_location_src_id': transit_location.id,
                'default_location_dest_id': stock_location.id,
                'sequence_code': 'WHIS',
                'company_id': self.company_id.id,
            },
            'interbranch_out_sparepart_type_id': {
                'name': _('Interbranch Out (Sparepart)'),
                'code': 'outgoing',
                'use_existing_lots': True,
                'use_create_lots': False,
                'sequence': max_sequence + 4,
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': transit_location.id,
                'sequence_code': 'WHOS',
                'company_id': self.company_id.id,
            },
        })
        return picking_type_create_values, max_sequence + 4

    def _get_picking_type_update_values(self):
        """Override to update interbranch picking type values for Unit and Sparepart divisions."""
        data = super()._get_picking_type_update_values()
        
        transit_location = self._get_transit_location()
        stock_location = self.lot_stock_id
        wh_code = self.code.replace(" ", "").upper()

        data.update({
            'interbranch_in_unit_type_id': {
                'default_location_src_id': transit_location.id,
                'default_location_dest_id': stock_location.id,
                'barcode': wh_code + "-IBIN",
            },
            'interbranch_out_unit_type_id': {
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': transit_location.id,
                'barcode': wh_code + "-IBOUT",
            },
            'interbranch_in_sparepart_type_id': {
                'default_location_src_id': transit_location.id,
                'default_location_dest_id': stock_location.id,
                'barcode': wh_code + "-IBINS",
            },
            'interbranch_out_sparepart_type_id': {
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': transit_location.id,
                'barcode': wh_code + "-IBOUTS",
            },
        })
        return data

    def _get_sequence_values(self):
        """Override to add interbranch sequence values for Unit and Sparepart divisions."""
        values = super()._get_sequence_values()
        company_code = str(self.company_id.code)
        values.update({
            'interbranch_in_unit_type_id': {
                'name': self.name + ' Interbranch In (Unit)',
                'prefix': 'WH/' + 'IN/' + company_code + '/%(y)s/%(month)s/',
                'padding': 5,
                'company_id': self.company_id.id,
            },
            'interbranch_out_unit_type_id': {
                'name': self.name + ' Interbranch Out (Unit)',
                'prefix': 'WH/' + 'OUT/' + company_code + '/%(y)s/%(month)s/',
                'padding': 5,
                'company_id': self.company_id.id,
            },
            'interbranch_in_sparepart_type_id': {
                'name': self.name + ' Interbranch In (Sparepart)',
                'prefix': 'WHS/' + 'IN/' + company_code + '/%(y)s/%(month)s/',
                'padding': 5,
                'company_id': self.company_id.id,
            },
            'interbranch_out_sparepart_type_id': {
                'name': self.name + ' Interbranch Out (Sparepart)',
                'prefix': 'WHS/' + 'OUT/' + company_code + '/%(y)s/%(month)s/',
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
