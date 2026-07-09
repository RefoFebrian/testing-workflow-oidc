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

class InheritStockPickingBatchQRCode(models.Model):
    _inherit = "stock.picking.batch"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('batch_line_ids')
    def _onchange_validate_duplicate_qr_code(self):
        """Validate duplicate qr_code in batch_line_ids."""
        if not self.batch_line_ids:
            return
        
        seen_qr_code = {}
        for line in self.batch_line_ids:
            if line.qr_code:
                if line.qr_code in seen_qr_code:
                    return {
                        'warning': {
                            'title': _("Warning"),
                            'message': _(f"QR Code '{line.qr_code}' sudah di input.\nMohon pilih QR Code lain."),
                        }
                    }
                seen_qr_code[line.qr_code] = True

    # 12: override methods

    # 13: action methods
    def action_confirm(self, auto_confirm=False):
        res = super(InheritStockPickingBatchQRCode, self).action_confirm(auto_confirm=auto_confirm)
        batch_line_ids = self.batch_line_ids
        if batch_line_ids:
            for line in batch_line_ids:
                if line.qr_code:
                    self.env['tw.qr.code.unit']._check_qr_code(line.qr_code, self.company_id.id)
                    move_line_obj = self.env['stock.move.line'].suspend_security().search([('lot_id', '=', line.lot_id.id)], limit=1)
                    if move_line_obj:
                        move_line_obj.suspend_security().write({'qr_code': line.qr_code})

        return res
  
    # 14: private methods

