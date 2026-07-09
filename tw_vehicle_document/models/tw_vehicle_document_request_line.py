# tw_document_handling/models/tw_vehicle_document_request_line.py

from odoo import models, fields, api, _

class TwVehicleDocumentRequestLine(models.Model):
    _name = "tw.vehicle.document.request.line"
    _inherit = ['vehicle.document.line.mixin']
    _description = "Permohonan Faktur Line"

    vehicle_document_request_id = fields.Many2one(
        'tw.vehicle.document.request', 
        string="Vehicle Document Request", 
        ondelete='cascade'
    )

    def action_cancel(self):
        cancel = super().action_cancel()
        for rec in self:
            rec.lot_id.suspend_security().write({
                'vehicle_document_request_id': False,
                'vehicle_document_request_date': False,
                'document_state': False
            })
        return cancel
