from odoo import api, models
from datetime import datetime
import time
import pytz

class TwDocumentMutationRegistrationReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_mutation.reg_mutation_report"
    _description = "Document Mutation Registration Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.document.mutation'].suspend_security().browse(docids)
        sequence = {'no': 0}

        def no_urut():
            sequence['no'] += 1
            return sequence['no']

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
            'doc_model': 'tw.document.mutation',
            'docs': docs,
            'no_urut': no_urut,
            'tgl': get_date,
            'usr': get_user,
            'time': time,
        }