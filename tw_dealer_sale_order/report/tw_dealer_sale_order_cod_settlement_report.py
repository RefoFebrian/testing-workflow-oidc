import pytz
from datetime import datetime
from odoo import models, api, _
from . import fungsi_terbilang


class PrintCODSettlementDealerSaleOrder(models.AbstractModel):
    _name = "report.tw_dealer_sale_order.cod_settlement_dso_template"
    _description = "Dealer Sale Order Report COD Settlement"
    
    def print_date(self, docdate):
        return docdate.strftime("%d-%m-%Y")
    
    def print_datetime(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")
    
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
            'print_date': self.print_date,
            'print_datetime': self.print_datetime,
            'terbilang': self.terbilang,
            'print_address': self.print_address,
            'settlement': docs.amount_total if docs.payment_type_id.name == 'Cash' else docs.amount_downpayment,
        }