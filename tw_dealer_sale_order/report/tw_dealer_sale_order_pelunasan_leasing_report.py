from odoo import models, fields, api, _
from datetime import datetime
from . import fungsi_terbilang


class PrintPelunasanLeasingDealerSaleOrder(models.AbstractModel):
    _name = "report.tw_dealer_sale_order.pelunasan_leasing_dso_template"
    _description = "Dealer Sale Order Report Pelunasan Leasing"
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
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
        docs = self.env['tw.dealer.sale.order'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'tw.dealer.sale.order',
            'docs': docs,
            'time_date': self.time_date,
            'terbilang': self.terbilang,
            'print_address': self.print_address,
        }