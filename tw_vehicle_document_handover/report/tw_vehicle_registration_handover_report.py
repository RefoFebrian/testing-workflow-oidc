from odoo import models, api
import time
from datetime import datetime
import pytz
from odoo.tools.translate import _
from odoo.tools.misc import format_date, format_datetime

class TwVehicleRegistrationHandoverReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_handover.reg_handover_report"
    _description = "Vehicle Registration Handover Report Parser"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.vehicle.registration.handover'].suspend_security().browse(docids)

        counter = 0
        def no_urut():
            nonlocal counter
            counter += 1
            return counter

        def local_time():
            now = datetime.now()
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(now.replace(tzinfo=pytz.utc)).astimezone(tz)
            start_date = start.strftime("%d-%m-%Y %H:%M")
            return start_date

        return {
            'doc_ids': docids,
            'doc_model': 'tw.vehicle.registration.handover',
            'docs': docs,
            'time': time,
            'datetime': datetime,
            'no_urut': no_urut,
            'local_time': local_time,
            'format_date': format_date,
            'format_datetime': format_datetime,
            '_': _,
        }