# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TwVehicleOwnershipReceiptCancelLine(models.Model):
    _name = "tw.vehicle.ownership.receipt.cancel.line"
    _description = 'Penerimaan BPKB Cancel Line'
    _order = 'id desc'
    
    cancel_id = fields.Many2one('tw.vehicle.ownership.receipt.cancel', 'Cancellation', ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', 'Engine No', required=True)
    chassis_number = fields.Char('Chassis Number', related='lot_id.chassis_number')
    
    @api.constrains('lot_id')
    def _check_lot_id(self):
        for rec in self:
            if rec.cancel_id.ownership_receipt_id:
                # Check for duplicate lots in the same cancellation
                duplicate_in_same_cancel = rec.cancel_id.cancel_line_ids.filtered(
                    lambda l: l.lot_id == rec.lot_id and l.id != rec.id
                )
                if duplicate_in_same_cancel:
                    raise ValidationError(_(
                        "This lot is already included in this cancellation."
                    ))
                
                # Check if lot exists in the receipt
                lot_in_receipt = self.env['tw.vehicle.ownership.receipt.line'].search([
                    ('vehicle_ownership_receipt_id', '=', rec.cancel_id.ownership_receipt_id.id),
                    ('lot_id', '=', rec.lot_id.id),
                    ('state', '!=', 'cancel')
                ], limit=1)
                
                if not lot_in_receipt:
                    raise ValidationError(_("The selected lot is not found in the ownership receipt or is already cancelled."))
                
                # Check if lot is already cancelled in another active cancellation
                existing_cancel = self.env['tw.vehicle.ownership.receipt.cancel'].search([
                    ('id', '!=', rec.cancel_id.id),
                    ('ownership_receipt_id', '=', rec.cancel_id.ownership_receipt_id.id),
                    ('state', 'in', ['draft', 'waiting_for_approval', 'approved', 'done']),
                    ('cancel_line_ids.lot_id', '=', rec.lot_id.id)
                ], limit=1)
                
                if existing_cancel:
                    state_name = dict(existing_cancel._fields['state'].selection).get(existing_cancel.state)
                    raise ValidationError(_(
                        "This lot is already included in another cancellation (%s) that is %s." % 
                        (existing_cancel.name, state_name)
                    ))