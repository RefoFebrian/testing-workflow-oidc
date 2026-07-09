import pytz
from datetime import datetime
from odoo import models, api, _
from odoo.addons.tw_web.report.fungsi_terbilang import terbilang


class PrintSettlementAdvancePaymentReport(models.AbstractModel):
    _name = "report.tw_payment_request.payment_request_report"
    _description = "Payment Report Report"
    
    def print_date(self, docdate):
        return docdate.strftime("%d-%m-%Y")
    
    def print_datetime(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")
    
    def terbilang(self, amount):
        return terbilang(amount, "idr", 'id')
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.payment.request'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.payment.request',
            'docs': docs,
            'print_date': self.print_date,
            'print_datetime': self.print_datetime,
            'terbilang': self.terbilang,
            'user': self.env.user
        }
        