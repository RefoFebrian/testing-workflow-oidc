# 1: imports of python lib
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning

class TwVehicleRegistrationCancelLine(models.Model):
    _name = "tw.registration.process.cancel.line"
    _description = "Proses STNK Cancel Line"
    _order = "id"

    # 7: defaults methods
    chassis_no = fields.Char(related='lot_id.chassis_number', string='Chassis No', readonly=True, store=True)
    
    # 8: fields
    cancel_id = fields.Many2one('tw.registration.process.cancel', string='Cancel Reference',ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', string='Engine No', required=True)
    
    @api.constrains('lot_id')
    def _check_lot_id(self):
        for rec in self:
            # Check for duplicate lots in the same cancellation
            duplicate_in_same_cancel = rec.cancel_id.vehicle_registration_cancel_line_ids.filtered(
                lambda l: l.lot_id == rec.lot_id and l.id != rec.id
            )
            if duplicate_in_same_cancel:
                raise ValidationError(_(
                    "This lot is already included in this cancellation."
                ))
            
            # Check if lot is already cancelled in another active cancellation
            existing_cancel = self.env['tw.registration.process.cancel'].search([
                ('id', '!=', rec.cancel_id.id),
                ('vehicle_registration_process_id', '=', rec.cancel_id.vehicle_registration_process_id.id),
                ('state', 'in', ['draft', 'waiting_for_approval', 'approved', 'done']),
                ('vehicle_registration_cancel_line_ids.lot_id', '=', rec.lot_id.id)
            ], limit=1)
            
            if existing_cancel:
                state_name = dict(existing_cancel._fields['state'].selection).get(existing_cancel.state)
                raise ValidationError(_(
                    "This lot is already included in another cancellation (%s) that is %s." % 
                    (existing_cancel.name, state_name)
                ))
    
    
