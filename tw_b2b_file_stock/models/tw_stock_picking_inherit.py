# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class B2bFileStockPickingInherit(models.Model):
    _inherit = "stock.picking"

    # 7: defaults methods

    # 8: fields
    mft_reference = fields.Char(string="MFT Reference", help="MFT Reference from ATPM")

    # Audit Trail

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    
    # 14: private methods
    def _get_to_store_picking(self):
        res = super()._get_to_store_picking()
        pickings = self._get_last_route_picking_sparepart_to_atpm()
        picking_without_fdo = pickings.filtered(lambda picking: (not picking.is_fdo_received()))
        to_store_pickings = picking_without_fdo + res
        return to_store_pickings

    def _get_to_validate_stored_picking(self):
        res = super()._get_to_validate_stored_picking()
        pickings = self._get_last_route_picking_sparepart_to_atpm()
        to_validate_pickings = pickings.filtered(lambda picking: (picking.state == 'stored' and picking.is_fdo_received()))
        stored_picking_with_fdo = to_validate_pickings + res
        return stored_picking_with_fdo
    
    #? B2B File methods for stored pickings
    def _get_last_route_picking_sparepart_to_atpm(self):
        # Mengambil Picking sparepart ke ATPM yang move nya berada di last route
        pickings = self.filtered(
            lambda picking: (
                picking.is_picking_sparepart_to_atpm() 
                and all(move._is_last_move_from_route() and not move.to_refund for move in picking.move_ids)
            )
        )
        return pickings
    
    def is_picking_sparepart_to_atpm(self):
        self.ensure_one()
        # Check apakah picking ini adalah picking dari pembelian (PO) sparepart dari MD ke ATPM
        md_code = self.env['res.company'].get_default_main_dealer_code()
        ahm_code = self.env['res.company'].get_default_main_dealer().default_supplier_id.code
        if all([
            self.company_id.code == md_code,
            self.partner_id.code == ahm_code,
            self.division == 'Sparepart'
        ]):
            return True
        return False

    def is_fdo_received(self):
        self.ensure_one()
        # Cek apakah Invoice Sparepart (FDO) sudah masuk, jika belum maka akan dibuat menjadi state stored
        total_qty_ps = self.env['tw.b2b.file.content']._get_total_qty(
            'PS', 'qty_ps', 'kode_ps', None, self.mft_reference
        )
        total_qty_fdo = self.env['tw.b2b.file.content']._get_total_qty(
            'FDO', 'qty', 'kode_ps', None, self.mft_reference
        )
        return total_qty_ps == total_qty_fdo
