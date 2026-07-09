# tw_document_handling/models/vehicle_document_line_mixin.py

from odoo import models, fields, api

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]

class VehicleDocumentLineMixin(models.AbstractModel):
    _name = "vehicle.document.line.mixin"
    _description = "Vehicle Document Line Mixin"

    chassis_number = fields.Char(related="lot_id.chassis_number", string='Chassis Number', store=True)
    state = fields.Selection(STATE_SELECTION, default='draft', readonly=True)
    
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Engine No', required=False)
    product_id = fields.Many2one(related="lot_id.product_id", store=True)
    partner_id = fields.Many2one(related="lot_id.partner_id", store=True)
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)
    

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.chassis_number = self.lot_id.chassis_number
            self.product_id = self.lot_id.product_id
            self.partner_id = self.lot_id.partner_id
            self.customer_stnk_id = self.lot_id.customer_stnk_id
    
    def action_cancel(self):
        for rec in self:
            rec.write({
                'state': 'cancel',
            })