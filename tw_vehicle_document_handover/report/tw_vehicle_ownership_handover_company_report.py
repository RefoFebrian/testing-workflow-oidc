from odoo import api, models, fields
from datetime import datetime
import pytz
import time
import base64
from odoo.tools.translate import _
from odoo.tools.misc import format_date, format_datetime

class TwVehicleOwnershipHandoverCompanyReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_handover.own_handover_report_company"
    _description = "Vehicle Ownership Handover Company Report Parser"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.vehicle.ownership.handover'].suspend_security().browse(docids)
        
        counter = 0
        def sequence_number():
            nonlocal counter
            counter += 1
            return counter

        return {
            'doc_ids': docids,
            'doc_model': 'tw.vehicle.ownership.handover',
            'docs': docs,
            'time': time,
            'datetime': datetime,
            'format_date': format_date,
            'format_datetime': format_datetime,
            '_': _,
            'sequence_number': sequence_number,
            'get_local_time': self.get_local_time,
            'update_print_count': self.update_print_count,
            'print_address': self.print_address,
        }

    def get_local_time(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")

    def update_print_count(self, doc):
        report_name = self._name
        report_xml = self.env['ir.actions.report']._get_report_from_name(report_name)
        
        if not report_xml:
            return ''

        report_id = report_xml.id
        model_id = self.env['ir.model'].search([('model', '=', doc._name)], limit=1).id
        JumlahCetak = self.env['tw.print.counter']
        
        jumlah_cetak_rec = JumlahCetak.search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', doc.id)
        ], limit=1)

        if not jumlah_cetak_rec:
            doc.write({'print_count': 1})
            jumlah_cetak_id = {
                'model_id': model_id,
                'transaction_id': doc.id,
                'jumlah_cetak': 1,
                'report_id': report_id
            }
            JumlahCetak.create(jumlah_cetak_id)
        else:
            cetakke = (doc.print_count or 0) + 1
            doc.write({'print_count': cetakke})
            
            jumlah_cetak = jumlah_cetak_rec.jumlah_cetak + 1
            jumlah_cetak_rec.write({'jumlah_cetak': jumlah_cetak})
            
        return ''
    
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
