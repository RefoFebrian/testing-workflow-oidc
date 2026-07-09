# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingQRCode(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _prepare_update_lot(self, picking, move, move_line):
        res = super(InheritStockPickingQRCode, self)._prepare_update_lot(picking, move, move_line)
        ahm_code = self.env['res.company'].get_default_main_dealer().default_supplier_id.code
        md_code = self.env['res.company'].get_default_main_dealer_code()
        if picking.company_id.code == md_code and picking.partner_id.code == ahm_code and move_line.qr_code and move_line.lot_id:
            res.update({'qr_code': move_line.qr_code})
            self._update_qr_code(move_line.qr_code, move_line.lot_id)
        return res

    def _update_qr_code(self, qr_code, lot_obj):
        qr_code_obj = self.env['tw.qr.code.unit'].sudo().search([('name', '=', qr_code)], limit=1)
        if qr_code_obj:
            if qr_code_obj.state == 'Linked' and qr_code_obj.lot_id != lot_obj:
                raise Warning(f"QR Code {qr_code} sudah terhubung dengan lot {qr_code_obj.lot_id.name}")

            qr_code_obj.write({
                'lot_id': lot_obj.id if lot_obj else False,
                'state': 'Linked'
            })

    # 14: private methods

