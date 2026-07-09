from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz
from . import fungsi_terbilang


class PrintInvoiceSaleOrder(models.AbstractModel):
    _name = "report.tw_sale.invoice_sale_order_template"
    _description = "Sales Order Report Invoice"

    def tax_label(self):
        sale_order = self.env['tw.sale.order'].browse(self.env.context.get('active_ids', []))
        return 'PPN %s' % int((sale_order.order_line[0].tax_id.amount or 0.11) * 100) if sale_order.order_line else "PPN 11%"
    
    def time_date(self):
        return datetime.now().strftime("%d-%m-%Y %H:%M")
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    def print_counter(self):
        model_id = self.env.ref('tw_sale.model_tw_sale_order').id
        report_id = self.env.ref('tw_sale.invoice_sale_order_report').id
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

    def get_invoice(self):
        so = self.env['tw.sale.order'].browse(self.env.context.get('active_ids', []))
        invoice = self.env['account.move'].search([('invoice_origin', '=', so.name)], order="id desc", limit=1)
        return invoice
    
    def get_payment_term(self, sale_order):
        payment_term = self.env['account.payment.term.line'].search([
            ("payment_id", "=", sale_order.payment_term_id.id)
        ], limit=1).nb_days
        return payment_term

    def get_payment_term_date(self):
        sale_order = self.env['tw.sale.order'].browse(self.env.context.get('active_ids', []))
        if not sale_order:
            return ""
        
        date_invoice = self.get_invoice().invoice_date if self.get_invoice() else None
        date_payment = self.get_payment_term(sale_order) if sale_order.payment_term_id else 0

        if not date_invoice:
            return ""
        
        date_commande = parse(str(date_invoice)).date()
        return (date_commande + timedelta(days=date_payment)).strftime("%d-%m-%Y")
    
    def get_dpp(self):
        amount_dpp = 0
        sale_order = self.env['tw.sale.order'].browse(self.env.context.get('active_ids', []))
        for line in sale_order.order_line:
            price = line.price_subtotal
            for tax in line.tax_id:
                price -= price * (1 - tax.amount)
            amount_dpp += price
        return round(amount_dpp, 2)
    
    def doc_line(self, order_line):
        lines = [(i+1, line) for i, line in enumerate(order_line)]
        return lines
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.sale.order'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.sale.order',
            'docs': docs,
            'invoice': self.get_invoice,
            'payment_term': self.get_payment_term,
            'payment_term_date': self.get_payment_term_date,
            'time_date': self.time_date,
            'terbilang': self.terbilang,
            'doc_line': self.doc_line,
            'print_counter': self.print_counter,
            'dpp': self.get_dpp,
        }