from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]

class TwVehicleRegistrationHandoverLine(models.Model):
    _name = "tw.vehicle.registration.handover.line"
    _description = "Penyerahan STNK Line"

    name = fields.Char(related="lot_id.name", store=True)
    notice_handover_date = fields.Date(string='Tanggal Ambil Notice')
    stnk_handover_date = fields.Date(string='Tanggal Ambil STNK')
    plate_handover_date = fields.Date(string='Tanggal Ambil Plat')
    chassis_number = fields.Char(related="lot_id.chassis_number", string='Nomor Chassis', store=True)
    notice_number = fields.Char(related='lot_id.notice_number')
    stnk_number = fields.Char(related='lot_id.vehicle_registration_number')
    plate_number = fields.Char(related='lot_id.plate_number')
    vehicle_registration_handover = fields.Boolean(string='STNK Sudah Diserahkan?', default=False)
    notice_handover = fields.Boolean(string='Notice Sudah Diserahkan?', default=False)
    plate_handover = fields.Boolean(string='Plat Sudah Diserahkan?', default=False)
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    
    vehicle_registration_handover_id = fields.Many2one('tw.vehicle.registration.handover', string="Penyerahan STNK", ondelete='cascade')
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Nomor Mesin', required=False)
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)

    @api.onchange('lot_id')
    def onchange_validation(self):
        self.vehicle_registration_handover = False
        self.notice_handover = False
        self.plate_handover = False

        if self.lot_id.notice_handover_date:
            self.notice_handover = True
            self.notice_handover_date = self.lot_id.notice_handover_date
        if self.lot_id.registration_handover_date:
            self.vehicle_registration_handover = True
            self.stnk_handover_date = self.lot_id.registration_handover_date
        if self.lot_id.plate_handover_date:
            self.plate_handover = True
            self.plate_handover_date = self.lot_id.plate_handover_date
    
    def action_cancel(self):
        for line in self:
            vals = {}
            if line.stnk_handover_date and line.lot_id.registration_handover_id:
                vals['registration_handover_date'] = False
                vals['registration_handover_id'] = False
                vals['registration_receiver'] = False
            if line.notice_handover_date and line.lot_id.notice_handover_id:
                vals['notice_handover_date'] = False
                vals['notice_handover_id'] = False
                vals['notice_receiver'] = False
            if line.plate_handover_date and line.lot_id.plate_handover_id:
                vals['plate_handover_date'] = False
                vals['plate_handover_id'] = False
                vals['plate_receiver'] = False
            if vals:
                line.lot_id.suspend_security().write(vals)

            line.suspend_security().write({
                'state': 'cancel',
            })