# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockMoveQrCode(models.Model):
    _inherit = "stock.move"
    
    # 7: defaults methods

    # 8: fields
    has_qr_code = fields.Selection([
        ('no', 'No'),
        ('yes', 'Yes')
    ], string='Has QR Code', default='no', compute='_compute_has_qr_code')
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('move_line_ids.lot_id', 'picking_id.picking_type_id', 'picking_id.picking_type_id.is_need_qr_code')
    def _compute_has_qr_code(self):
        for record in self:
            record.has_qr_code = 'yes' if record.picking_id.picking_type_id.is_need_qr_code else 'no'
    
    @api.onchange('move_line_ids')
    def _onchange_validate_duplicate_qr_code(self):
        """Validate duplicate qr_code in move_line_ids."""
        if not self.move_line_ids:
            return
        
        seen_qr_code = {}
        for line in self.move_line_ids:
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

    # 14: private methods
    
