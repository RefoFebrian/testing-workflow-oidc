from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwVehicleDocumentLocation(models.Model):
    _name = "tw.vehicle.document.location"
    _description = "Vehicle Document Location"

    name = fields.Char(string="Location Name", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    address = fields.Char(string="Address")

    document_type = fields.Selection(
        selection=[
            ('vehicle_registration', 'STNK'),
            ('vehicle_ownership', 'BPKB'),
        ],string='Document Type'
    )
    type = fields.Selection(selection=[
            ('internal', 'Internal Location'),
            ('transit','Transit Location')
        ], string='Location Type')

    city_id = fields.Many2one(comodel_name='res.city', string='City', required=False)
    company_id = fields.Many2one('res.company', string='Branch', required=True)