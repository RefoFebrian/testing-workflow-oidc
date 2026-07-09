from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]

class TwVehicleRegistrationReceiptLine(models.Model):
    _name = "tw.vehicle.registration.receipt.line"
    _description = "Registration Receipt Line"

    name = fields.Char(related="lot_id.name", store=True)
    notice_number = fields.Char(string='Notice Number',)
    notice_date = fields.Date(string='Notice Date', required=False)
    vehicle_registration_number = fields.Char(string='STNK Number',)
    stnk_date = fields.Date(string='STNK Date', required=False)
    plate_number = fields.Char(string='Plate Number', required=False)
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    chassis_number = fields.Char(related="lot_id.chassis_number", string='Chassis Number', store=True)
    
    is_receive_plate = fields.Boolean(string='Is Receive Plate?', required=False)
    vehicle_registration_received = fields.Boolean(string='Is STNK received?', default=False)
    notice_received = fields.Boolean(string='Is STNK Notice received?', default=False)
    plate_received = fields.Boolean(string='Is Plate received?', default=False)
    
    vehicle_registration_receipt_id = fields.Many2one('tw.vehicle.registration.receipt', string="Registration Receipt", ondelete='cascade')
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Engine No', required=False)
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)

    @api.onchange('notice_number', 'vehicle_registration_number', 'plate_number')
    def onchange_validation(self):
        if self.notice_number:
            self.notice_number = self.notice_number.replace(' ', '').upper()
        if self.vehicle_registration_number:
            self.vehicle_registration_number = self.vehicle_registration_number.replace(' ', '').upper()
        if self.plate_number:
            self.plate_number = self.plate_number.replace(' ', '').upper()

    @api.onchange('lot_id')
    def onchange_lot(self):
        if self.lot_id.notice_receipt_id:
            self.notice_received = True
        if self.lot_id.vehicle_registration_receipt_id:
            self.vehicle_registration_received = True
        if self.lot_id.plate_receipt_id:
            self.plate_received = True
            self.is_receive_plate = True
        self.notice_number = self.lot_id.notice_number
        self.notice_date = self.lot_id.notice_date
        self.vehicle_registration_number = self.lot_id.vehicle_registration_number
        self.stnk_date = self.lot_id.stnk_date
        self.plate_number = self.lot_id.plate_number

        # Auto-compute notice_date dari tgl proses STNK + 1 tahun jika belum terisi
        if not self.notice_date and self.lot_id.registration_process_date:
            self.notice_date = self.lot_id.registration_process_date + relativedelta(years=1)

    @api.onchange('notice_date')
    def _onchange_notice_date(self):
        if self.notice_date:
            self.stnk_date = self.notice_date + relativedelta(years=4)
    
    def action_registration_receipt_cancel(self):
        """Clear STNK data on stock.lot without changing receipt line state."""
        for line in self:
            if line.lot_id.vehicle_registration_receipt_id:
                line.lot_id.suspend_security().write({
                    'vehicle_registration_receipt_id': False,
                    'vehicle_registration_receipt_date': False,
                    'vehicle_registration_location_id': False,
                    'vehicle_registration_number': False,
                    'stnk_date': False,
                    'plate_number': False,
                })

    def action_notice_receipt_cancel(self):
        """Clear Notice data on stock.lot without changing receipt line state."""
        for line in self:
            if line.lot_id.notice_receipt_id:
                line.lot_id.suspend_security().write({
                    'notice_receipt_id': False,
                    'notice_receipt_date': False,
                    'notice_number': False,
                    'notice_date': False,
                })

    def action_plate_receipt_cancel(self):
        """Clear Plate data on stock.lot without changing receipt line state."""
        for line in self:
            if line.lot_id.plate_receipt_id:
                line.lot_id.suspend_security().write({
                    'plate_receipt_id': False,
                    'plate_receipt_date': False,
                })
