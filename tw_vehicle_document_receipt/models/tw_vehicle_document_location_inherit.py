from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwVehicleDocumentLocationInherit(models.Model):
    _inherit = "tw.vehicle.document.location"

    lot_registration_ids = fields.One2many(comodel_name='stock.lot', inverse_name='vehicle_registration_location_id', string="Engine No", domain="[('registration_handover_id', '=', False)]")
    lot_ownership_ids = fields.One2many(comodel_name='stock.lot', inverse_name='vehicle_ownership_location_id', string='Engine No', domain="[('ownership_handover_id', '=', False)]")