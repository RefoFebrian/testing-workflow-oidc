from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TwSupplierPaymentBusinessTrip(models.Model):
    _inherit = "tw.account.payment"

    def action_validate(self):
        business_trip = self.env['tw.business.trip'].suspend_security().search([('supplier_payment_id', '=', self.id)])
        if business_trip:
            business_trip.suspend_security().action_done()
        super().action_validate()
