from odoo import models, api
from odoo.exceptions import UserError
from . import fungsi_terbilang 
import pytz 
from datetime import datetime 

class ReportOtherReceivable(models.AbstractModel):
    _name = "report.tw_other_receivable.report_kwitansi_other_receivable"
    _description = 'Laporan Other Receivable'

    def get_local_time(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")

    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")
    
    def print_user(self):
        user_obj = self.env['res.users'].suspend_security().browse(self.env.uid)
        return user_obj.name or ''
    
    def print_employee(self, user_id):
        emp_obj = self.env['hr.employee'].suspend_security().search([('user_id','=',user_id)])
        return emp_obj.name or ''
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')

    def print_counter(self):
        model_id = self.env.ref('tw_payment.model_tw_account_payment').id
        report_id = self.env.ref('tw_payment.action_report_tw_payment_kwitansi').id
        transaction_id = self.env.context.get('active_ids', [])[0]

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', transaction_id)
        ], limit=1)

        payment_obj = self.env['tw.other.receivable'].sudo().browse(transaction_id)
        if payment_obj:
            payment_obj.write({'receipt_print_count': int(payment_obj.receipt_print_count) + 1})

        if not print_obj:
            print_count_obj = self.env['tw.print.counter'].sudo().create({
                'model_id': model_id,
                'transaction_id': transaction_id,
                'print_counter': 1,
                'kwitansi_line_id': payment_obj.register_kwitansi_line_id.id,
                'report_id': report_id
            })
            return print_count_obj.print_counter
        else:
            print_obj.write({'print_counter': print_obj.print_counter + 1})


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.other.receivable'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.other.receivable',
            'docs': docs,
            'print_counter':self.print_counter,
            'time_date': self.time_date,
            'print_user': self.print_user,
            'print_employee': self.print_employee,
            'terbilang': self.terbilang,
            'get_local_time':self.get_local_time,
        }