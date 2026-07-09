from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz
from . import fungsi_terbilang


class PrintInvoiceDealerSaleOrder(models.AbstractModel):
    _name = "report.tw_dealer_sale_order.invoice_dso_template"
    _description = "Dealer Sales Order Report Invoice"
    
    def doc_line(self, order_line):
        lines = [(i+1, line) for i, line in enumerate(order_line)]
        return lines
    
    def time_date(self, date):
        if date:
            return date.strftime("%d-%m-%Y")
        return ""
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    def print_counter(self):
        model_id = self.env.ref('tw_dealer_sale_order.model_tw_dealer_sale_order').id
        report_id = self.env.ref('tw_dealer_sale_order.invoice_dealer_sale_order_report').id
        transaction_id = self.env.context.get('active_ids', [])[0]

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', transaction_id)
        ], limit=1)

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
    
    def get_payment_term(self, dso):
        payment_term = self.env['account.payment.term.line'].search([
            ("payment_id", "=", dso.payment_term_id.id)
        ], limit=1).nb_days
        return payment_term
    
    def get_total_product_quantity(self, dso):
        return sum([line.product_uom_qty for line in dso.order_line.filtered(lambda l: l.product_id)])
    
    def get_total_subtotal(self, dso):
        return sum([line.price_unit * line.product_uom_qty for line in dso.order_line.filtered(lambda l: l.product_id)])
    
    def get_total(self, dso):
        return sum([line.price_total for line in dso.order_line.filtered(lambda l: l.product_id)])

    def get_dpp(self):
        amount_dpp = 0
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        for line in dso.order_line:
            price = line.price_subtotal
            for tax in line.tax_id:
                # Perhitungan DPP 11/12 (DPP Nilai Lain)
                price = price * tax.tax_base_amount
            amount_dpp += price
        return round(amount_dpp, 2)
    
    def get_invoice(self):
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        invoice = self.env['account.move'].search([('invoice_origin', '=', dso.name)], order="id desc", limit=1)
        return invoice
    
    def date_invoice(self):
        invoice_obj = self.get_invoice()

        date_invoice = datetime.today().strftime('%d-%m-%Y')
        if invoice_obj and invoice_obj.invoice_date:
            date_invoice = invoice_obj.invoice_date.strftime('%d-%m-%Y')

        return date_invoice
    
    def due_date_invoice(self):
        invoice_obj = self.get_invoice()

        date_invoice = datetime.today().strftime('%d-%m-%Y')
        if invoice_obj and invoice_obj.invoice_date:
            date_invoice = invoice_obj.invoice_date.strftime('%d-%m-%Y')

        date_commande = parse(str(date_invoice)).date()

        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        payment_term_date = self.get_payment_term(dso)
        return (date_commande + timedelta(days=int(payment_term_date))).strftime("%d-%m-%Y")
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.dealer.sale.order'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.dealer.sale.order',
            'docs': docs,
            'doc_line': self.doc_line,
            'get_payment_term': self.get_payment_term,
            'time_date': self.time_date,
            'terbilang': self.terbilang,
            'dpp': self.get_dpp,
            'print_counter': self.print_counter,
            'total_quantity': self.get_total_product_quantity,
            'date_invoice': self.date_invoice,
            'due_date_invoice': self.due_date_invoice,
            'print_address': self.print_address,
            'total_subtotal': self.get_total_subtotal,
            'total': self.get_total,
        }