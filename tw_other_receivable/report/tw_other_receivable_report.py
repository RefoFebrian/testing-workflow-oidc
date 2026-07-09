# 1: imports of python lib
from datetime import datetime

# 3: imports of odoo
from odoo import models, api

# 5: local imports
from . import fungsi_terbilang

# 6: Import of unknown third party lib
import pytz


class ReportOtherReceivablePrint(models.AbstractModel):
    _name = "report.tw_other_receivable.report_other_receivable_print"
    _description = "Laporan Piutang Lain-Lain"

    def get_local_time(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")

    def print_employee(self, user_id):
        emp_obj = self.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
        return emp_obj.name or ''

    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')

    def print_counter(self, doc_id):
        model_id = self.env.ref('tw_other_receivable.model_tw_other_receivable').id
        report_id = self.env.ref('tw_other_receivable.action_report_other_receivable_print').id

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', doc_id)
        ], limit=1)

        receivable_obj = self.env['tw.other.receivable'].sudo().browse(doc_id)
        if receivable_obj:
            receivable_obj.write({'receipt_print_count': int(receivable_obj.receipt_print_count) + 1})

        if not print_obj:
            print_count_obj = self.env['tw.print.counter'].sudo().create({
                'model_id': model_id,
                'transaction_id': doc_id,
                'print_counter': 1,
                'report_id': report_id
            })
            return print_count_obj.print_counter
        else:
            print_obj.write({'print_counter': print_obj.print_counter + 1})
            return print_obj.print_counter

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.other.receivable'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.other.receivable',
            'docs': docs,
            'terbilang': self.terbilang,
            'get_local_time': self.get_local_time,
            'print_employee': self.print_employee,
            'print_counter': self.print_counter,
        }