from odoo import models, api, _
from . import fungsi_terbilang
import pytz 
from datetime import datetime 

class CustomerPaymentReport(models.AbstractModel):
    _name = "report.tw_payment.report_tw_customer_payment"
    _description = "Customer Payment Report"
    
    def doc_line(self, move_line):
        lines = [(i+1, line) for i, line in enumerate(move_line)]
        return lines

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
    
    def print_address(self, partner):
        address = partner.street or ''
        if partner.street2:
            address += f', {partner.street2}'
        if partner.rt and partner.rw:
            address += f', RT/RW {partner.rt}/{partner.rw}'
        if partner.sub_district_id:
            address += f', Kel. {partner.sub_district_id.name.title()}'
        if partner.district_id:
            address += f', Kec. {partner.district_id.name.title()}'
        if partner.city_id:
            address += f', {partner.city_id.name.title()}'
        if partner.state_id:
            address += f', {partner.state_id.name.title()}'
        if partner.zip:
            address += f', {partner.zip}'
        return address
    
    def get_reference_transaction(self, payment_id, transaction_type):
        payment_line = self.env['tw.account.payment.line'].suspend_security().search([
            ('payment_id','=',payment_id),
            ('type','=','cr')
        ])
    
        reference = ""

        if transaction_type == 'reference':
            if len(payment_line) > 1:
                for pl in payment_line:
                    reference += f"{pl.move_line_id.ref}, "
            else:
                return payment_line.move_line_id.ref
        elif transaction_type == 'kwitansi':
            if len(payment_line) > 1:
                for pl in payment_line:
                    reference += f"{pl.move_line_id.move_name}, "
            else:
                return payment_line.move_line_id.move_name

        return reference
    
    def print_counter(self, trx_id=None):
        model_id = self.env.ref('tw_payment.model_tw_account_payment').id
        report_id = self.env.ref('tw_payment.action_report_tw_payment_kwitansi').id
        if not self.env.context.get('active_ids', []) and trx_id:
            transaction_id = trx_id
        else:
            transaction_id = self.env.context.get('active_ids', [])[0]

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', transaction_id)
        ], limit=1)

        payment_obj = self.env['tw.account.payment'].sudo().browse(transaction_id)
        if payment_obj:
            payment_obj.write({'receipt_print_count': int(payment_obj.receipt_print_count) + 1})

        if not print_obj:
            print_count_obj = self.env['tw.print.counter'].sudo().create({
                'model_id': model_id,
                'transaction_id': transaction_id,
                'print_counter': 1,
                'report_id': report_id
            })
            return print_count_obj.print_counter
        else:
            print_obj.write({'print_counter': print_obj.print_counter + 1})

        return print_obj.print_counter
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.account.payment'].browse(docids)
        if not docs:
            if data and data.get('id'):
                docs = self.env['tw.account.payment'].browse(data['id'])
        return {
            'doc_ids': docids,
            'doc_model': 'tw.account.payment',
            'docs': docs,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_counter': self.print_counter,
            'print_user': self.print_user,
            'print_employee': self.print_employee,
            'get_reference_transaction': self.get_reference_transaction,
            'terbilang': self.terbilang,
            'get_local_time':self.get_local_time,
            'print_address': self.print_address
        }