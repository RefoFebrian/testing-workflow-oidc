from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]

class TwVehicleOwnershipHandoverLine(models.Model):
    _name = "tw.vehicle.ownership.handover.line"
    _description = "Penyerahan BPKB Line"

    name = fields.Char(related="lot_id.name", store=True)
    ownership_handover_date = fields.Date(string='Tgl Ambil BPKB', required=False)
    chassis_number = fields.Char(related="lot_id.chassis_number", string='Chassis Number', store=True)
    bpkb_number = fields.Char(related='lot_id.vehicle_ownership_number')
    bpkb_order_number = fields.Char(related='lot_id.vehicle_ownership_order_number')
    
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    
    ownership_handover_id = fields.Many2one('tw.vehicle.ownership.handover', string="Penyerahan BPKB", ondelete='cascade')
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Engine No', required=False)
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)

    def action_cancel(self):
        for line in self:
            line.lot_id.suspend_security().write({
                'ownership_handover_id': False,
                'ownership_handover_date': False,
                'ownership_receiver': False,
            })
            line.suspend_security().write({
                'state': 'cancel',
            })
