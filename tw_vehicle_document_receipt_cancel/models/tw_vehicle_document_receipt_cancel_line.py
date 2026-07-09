# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class TwVehicleDocumentReceiptCancelLine(models.Model):
    _name = "tw.vehicle.document.receipt.cancel.line"
    _description = "Penerimaan STNK Cancel Line"
    
    cancel_id = fields.Many2one('tw.vehicle.document.receipt.cancel', 'Cancellation', ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', 'Engine No', required=True)
    chassis_number = fields.Char('Chassis Number', related='lot_id.chassis_number')
    
    @api.constrains('lot_id')
    def _check_lot_id(self):
        for rec in self:
        # Check for duplicate lots in the same cancellation
            duplicate_in_same_cancel = rec.cancel_id.cancel_line_ids.filtered(
                lambda l: l.lot_id == rec.lot_id and l.id != rec.id
            )
            if duplicate_in_same_cancel:
                raise ValidationError(_(
                    "This lot is already included in this cancellation."
                ))
        
            # Check if lot is already cancelled in another cancellation
            existing_cancel_line = self.env['tw.vehicle.document.receipt.cancel.line'].search([
                ('id', '!=', rec.id),
                ('lot_id', '=', rec.lot_id.id),
                ('cancel_id.vehicle_document_receipt_id', '=', rec.cancel_id.vehicle_document_receipt_id.id),
                ('cancel_id.state', 'not in', ['draft', 'cancel'])
            ], limit=1)
            
            if existing_cancel_line:
                raise ValidationError(_(
                    "This lot is already included in another cancellation (%s) that is %s." % 
                    (existing_cancel_line.cancel_id.name, 
                    dict(existing_cancel_line.cancel_id._fields['state'].selection).get(existing_cancel_line.cancel_id.state))
                ))
