from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TwSettlementBusinessTrip(models.Model):
    _inherit = "tw.settlement"

    def action_confirm(self):
        business_trip = self.env['tw.business.trip'].suspend_security().search([('settlement_id', '=', self.id)])
        if business_trip:
            business_trip.suspend_security().action_done()
        super().action_confirm()
