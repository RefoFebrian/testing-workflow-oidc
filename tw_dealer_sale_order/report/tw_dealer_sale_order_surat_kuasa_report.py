from odoo import models, fields, api, _
from datetime import datetime
from . import fungsi_terbilang

from odoo.exceptions import UserError as Warning

class PrintSuratKuasaDealerSaleOrder(models.AbstractModel):
    _name = "report.tw_dealer_sale_order.surat_kuasa_dso_template"
    _description = "Dealer Sale Order Report Surat Kuasa"
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    def get_power_of_attorney(self):
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))

        if dso.power_of_attorney_type == 'SOH':
            soh = self.env['hr.employee'].sudo().search([
                ('company_id','=',dso.company_id.id),
                ('job_id.sales_force_id.value','=','sales_operation_head'),
                ('active','=',True)],limit=1)
            if not soh:
                raise Warning('Sales Operation Head data not found.')
            return soh
        else:
            return dso.order_line[0].biro_jasa_id
    
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
        
    def get_power_of_attorney_name(self):
        power_of_attorney_obj = self.get_power_of_attorney()
        return power_of_attorney_obj.name

    def get_power_of_attorney_job(self, type):
        power_of_attorney_obj = self.get_power_of_attorney()
        return power_of_attorney_obj.job_id.name if type == 'SOH' else 'Birojasa'

    def get_power_of_attorney_street(self, type):
        power_of_attorney_obj = self.get_power_of_attorney()
        partner = power_of_attorney_obj.user_partner_id if type == 'SOH' else power_of_attorney_obj
        return self.print_address(partner)
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.dealer.sale.order'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.dealer.sale.order',
            'docs': docs,
            'time_date': self.time_date,
            'terbilang': self.terbilang,
            'power_of_attorney_name': self.get_power_of_attorney_name,
            'power_of_attorney_job': self.get_power_of_attorney_job,
            'power_of_attorney_street': self.get_power_of_attorney_street,
            'print_address': self.print_address,
        }