import time
from datetime import datetime
from odoo import api, fields, models, _
import pytz

class TwBirojasaReport(models.AbstractModel):
    _name = "report.tw_birojasa_billing_process.birojasa_report"
    _description = "Birojasa Billing Report"

    def waktu_local(self):
        minute = datetime.now()
        return fields.Datetime.context_timestamp(self, minute).strftime("%d-%m-%Y %H:%M")

    def jumlah_cetakan(self, docs):
        
        if not docs:
            return 0
        
        active_id = docs.id

        printed_amount_obj = self.env['tw.print.counter']
        model = self.env['ir.model'].suspend_security().search([('model', '=', 'tw.birojasa.billing.process')], limit=1)

        report_name = self._name.replace('report.', '')
        report = self.env['ir.actions.report'].suspend_security().search([('report_name', '=', report_name)], limit=1)
        
        if not report:
            report = self.env['ir.actions.report'].suspend_security().search([('model', '=', 'tw.birojasa.billing.process')], limit=1)

        if not report:
            return 1

        printed_amount = printed_amount_obj.suspend_security().search([
            ('report_id', '=', report.id),
            ('model_id', '=', model.id),
            ('transaction_id', '=', active_id)
        ])
        
        if not printed_amount:
            printed_amount_vals = {
                'model_id': model.id,
                'transaction_id': active_id,
                'print_counter': 1,
                'report_id': report.id
            }
            print_counter = 1
            printed_amount_obj.create(printed_amount_vals)
        
        else:
            print_counter = printed_amount.print_counter + 1
            printed_amount.write({'print_counter': print_counter})
        
        return print_counter

    def correction_amount(self, docs):
        if not docs:
            return 0.0
        return sum(line.correction_amount for line in docs.billing_line_ids)

    def progressive_amount(self, docs):
        if not docs:
            return 0.0

        return sum(line.progressive_tax_amount for line in docs.billing_line_ids)

    def bill_amount(self, docs):
        if not docs:
            return 0.0

        return sum(line.amount_total for line in docs.billing_line_ids)

    def accrue_amount(self, docs):
        if not docs:
            return 0.0

        return sum(line.estimation_amount for line in docs.billing_line_ids)
    
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
        
    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'tw.birojasa.billing.process'
        docs = self.env[model].suspend_security().browse(docids)
        
        counter = {'no': 0}
        def no_urut():
            counter['no'] += 1
            return counter['no']

        if data is None:
            data = {}

        user_name = self.env.user.name
        if data.get('user'):
            user_name = data['user']

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'data': data,
            'no_urut': no_urut,
            'user': user_name,
            'time': time,
            'waktu_local': self.waktu_local,
            'correction_amount': lambda: self.correction_amount(docs),
            'progressive_amount': lambda: self.progressive_amount(docs),
            'bill_amount': lambda: self.bill_amount(docs),
            'accrue_amount': lambda: self.accrue_amount(docs),
            'jumlah_cetakan': lambda: self.jumlah_cetakan(docs),
            'print_address': self.print_address
        }