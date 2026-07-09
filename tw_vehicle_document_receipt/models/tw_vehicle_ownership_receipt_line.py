from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleOwnershipReceiptLine(models.Model):
    _name = "tw.vehicle.ownership.receipt.line"
    _description = "Vehicle Ownership Receipt Line"

    name = fields.Char(related="lot_id.name", store=True)
    vehicle_ownership_number = fields.Char(string='Vehicle Ownership Number')
    vehicle_ownership_date = fields.Date(string='Vehicle Ownership Date')
    vehicle_ownership_order_number = fields.Char(string='Nomor Urut BPKB', compute='_compute_ownership_order_number', store=True)
    chassis_number = fields.Char(related="lot_id.chassis_number", string='Chassis Number', store=True)
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    
    vehicle_ownership_receipt_id = fields.Many2one('tw.vehicle.ownership.receipt', string="Vehicle Ownership Receipt", ondelete='cascade')
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Engine No')
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)

    @api.depends('lot_id')
    def _compute_ownership_order_number(self):
        seq_name = 'BP'
        sequence = self.env['ir.sequence'].search([('name', '=', seq_name)], limit=1)
        
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': seq_name,
                'code': 'tw.vehicle.ownership.receipt.sequence',
                'prefix': 'BP',
                'padding': 8,
            })
        
        for record in self:
            if not record.create_date:
                record.vehicle_ownership_order_number = sequence.next_by_id()
    
    @api.onchange('vehicle_ownership_number', 'vehicle_ownership_order_number')
    def onchange_validation(self):
        if self.vehicle_ownership_number:
            self.vehicle_ownership_number = self.vehicle_ownership_number.replace(' ', '').upper()
        if self.vehicle_ownership_order_number:
            self.vehicle_ownership_order_number = self.vehicle_ownership_order_number.replace(' ', '').upper()

    def action_cancel(self): 
        for line in self:
            line.lot_id.suspend_security().write({
                    'vehicle_ownership_receipt_id': False,
                    'vehicle_ownership_receipt_date': False,
                    'vehicle_ownership_location_id': False,
                    'vehicle_ownership_number': False,
                    'vehicle_ownership_order_number': False,
                    'vehicle_ownership_date': False,
                })
            line.suspend_security().write(
                {'state': 'cancel'}
            )
