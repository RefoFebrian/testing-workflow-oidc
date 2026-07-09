from odoo import api, models
from datetime import datetime
import time
import pytz

class TwDocumentMutationOwnershipRequestReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_mutation.own_mutation_request_report"
    _description = "Document Mutation Ownership Request Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.ownership.mutation.request'].suspend_security().browse(docids)

        def get_date():
            menit = datetime.now()
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(menit).astimezone(tz)
            return start.strftime("%Y-%m-%d %H:%M")

        def get_user():
            return self.env.user.name
        
        def print_address(partner):
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
            

        return {
            'doc_ids': docids,
            'doc_model': 'tw.ownership.mutation.request',
            'docs': docs,
            'tgl': get_date,
            'usr': get_user,
            'print_address': print_address,
            'time': time,
        }