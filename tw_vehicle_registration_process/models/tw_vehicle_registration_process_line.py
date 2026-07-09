from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]
class TwVehicleRegistrationProcessLine(models.Model):
    _name = "tw.vehicle.registration.process.line"
    _description = "Proses STNK Detail"

    name = fields.Char(related="lot_id.name", store=True)
    chassis_number = fields.Char(related="lot_id.chassis_number", string='Chassis Number', store=True)
    doc_number = fields.Char(string='No Faktur STNK', related='lot_id.doc_number')
    vehicle_document_request_date = fields.Date(string='Request Date', related='lot_id.vehicle_document_request_date')
    vehicle_document_receive_date = fields.Date(string='Receive Date', related='lot_id.vehicle_document_receive_date')
    state = fields.Selection(STATE_SELECTION, default="draft", readonly=True)
    
    registration_process_id = fields.Many2one('tw.vehicle.registration.process', string="STNK Process", ondelete='cascade')
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Engine No', required=False)
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)

    def action_cancel(self):
        for rec in self:
            rec.suspend_security().write({
                'state': 'cancel',
            })
            rec.lot_id.suspend_security().write({
                'registration_process_id': False,
                'registration_process_date': False,
                'document_state': 'document_receive'
            })
