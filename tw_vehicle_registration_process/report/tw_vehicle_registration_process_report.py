from odoo import models, api, fields
from datetime import datetime
import pytz

class TwVehicleRegistrationProcessReport(models.AbstractModel):
    _name = "report.tw_vehicle_registration_process.print_out_registration"
    _description = "Proses STNK Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.vehicle.registration.process'].suspend_security().browse(docids)

        def default_local_time():
            menit = datetime.now()
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(menit).astimezone(tz)
            return start.strftime("%d-%m-%Y %H:%M")

        return {
            'doc_ids': docids,
            'doc_model': 'tw_vehicle_registration_process',
            'docs': docs,
            'local_time': default_local_time,
        }