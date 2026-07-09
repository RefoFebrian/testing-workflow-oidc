# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwVehicleDocumentCancelLine(models.Model):
    _name = "tw.vehicle.document.cancel.line"
    _description = 'Vehicle Document Cancel Line'
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields
    chassis_no = fields.Char('Chassis No', related='lot_id.chassis_number')
    
    # 9: relation fields
    cancel_id = fields.Many2one('tw.vehicle.document.cancel', 'Cancel')
    lot_id = fields.Many2one('stock.lot', 'Engine No', required=True)

    @api.constrains('lot_id')
    def _check_lot_id(self):
        for rec in self:
            # Check for duplicate lots in the same cancellation
            duplicate_in_same_cancel = rec.cancel_id.vehicle_document_cancel_line_ids.filtered(
                lambda l: l.lot_id == rec.lot_id and l.id != rec.id
            )
            if duplicate_in_same_cancel:
                raise ValidationError(_(
                    "This lot is already included in this cancellation."
                ))
            
            # Check if lot is already cancelled in another active cancellation
            domain = [
                ('id', '!=', rec.cancel_id.id),
                ('state', 'in', ['draft', 'waiting_for_approval', 'approved', 'done']),
                ('vehicle_document_cancel_line_ids.lot_id', '=', rec.lot_id.id)
            ]
            
            # Add conditions based on whether it's a request or receive cancellation
            if rec.cancel_id.vehicle_document_request_id:
                domain.append(('vehicle_document_request_id', '=', rec.cancel_id.vehicle_document_request_id.id))
            elif rec.cancel_id.vehicle_document_receive_id:
                domain.append(('vehicle_document_receive_id', '=', rec.cancel_id.vehicle_document_receive_id.id))
            
            existing_cancel = self.env['tw.vehicle.document.cancel'].search(domain, limit=1)
            
            if existing_cancel:
                state_name = dict(existing_cancel._fields['state'].selection).get(existing_cancel.state)
                raise ValidationError(_(
                    "This lot is already included in another cancellation (%s) that is %s." % 
                    (existing_cancel.name, state_name)
                ))
    
    