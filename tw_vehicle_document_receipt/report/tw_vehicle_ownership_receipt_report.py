from odoo import models, api, fields
from datetime import datetime
import pytz

class TwVehicleOwnershipReceiptReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_receipt.own_receipt_report"
    _description = "Vehicle Ownership Receipt Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.vehicle.ownership.receipt'].suspend_security().browse(docids)
        
        counter = 0
        def no_urut():
            nonlocal counter
            counter += 1
            return counter

        def get_date():
            menit = datetime.now()
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(menit).astimezone(tz)
            return start.strftime("%Y-%m-%d %H:%M")

        def get_user():
            return self.env.user.name

        return {
            'doc_ids': docids,
            'doc_model': 'tw.vehicle.ownership.receipt',
            'docs': docs,
            'no_urut': no_urut,
            'date': get_date,
            'usr': get_user,
        }