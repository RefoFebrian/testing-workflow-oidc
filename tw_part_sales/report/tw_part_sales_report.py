from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz
from . import fungsi_terbilang


class PrintInvoicePartSales(models.AbstractModel):
    _name = "report.tw_part_sales.invoice_part_sales_template"
    _description = "Part Sales Report Invoice"

    no = fields.Char('no')

    def tax_label(self):
        part_sales = self.env['tw.part.sales'].browse(self.env.context.get('active_ids', []))
        return 'PPN %s' % int((part_sales.order_line[0].tax_id.amount or 0.11) * 100) if part_sales.order_line else "PPN 11%"
    
    def no_urut(self):
        if not hasattr(self, 'no'):
            self.no = 0
        self.no += 1
        return self.no
    
    def time_date(self):
        return datetime.now().strftime("%d-%m-%Y %H:%M")
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    def print_counter(self):
        model_id = self.env.ref('tw_part_sales.model_tw_part_sales').id
        report_id = self.env.ref('tw_part_sales.invoice_part_sales_report').id
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
        ps = self.env['tw.part.sales'].browse(self.env.context.get('active_ids', []))
        invoice = self.env['account.move'].search([('invoice_origin', '=', ps.name)], order="id desc", limit=1)
        return invoice
    
    def get_payment_term(self, part_sales):
        payment_term = self.env['account.payment.term.line'].search([
            ("payment_id", "=", part_sales.payment_term_id.id)
        ], limit=1).nb_days
        return payment_term

    def get_payment_term_date(self):
        part_sales = self.env['tw.part.sales'].browse(self.env.context.get('active_ids', []))
        if not part_sales:
            return ""
        
        date_invoice = self.get_invoice().invoice_date if self.get_invoice() else None
        date_payment = self.get_payment_term(part_sales) if part_sales.payment_term_id else 0

        if not date_invoice:
            return ""
        
        date_commande = parse(str(date_invoice)).date()
        return (date_commande + timedelta(days=date_payment)).strftime("%d-%m-%Y")
    
    def get_dpp(self):
        amount_dpp = 0
        part_sales = self.env['tw.part.sales'].browse(self.env.context.get('active_ids', []))
        for line in part_sales.order_line:
            price = line.price_subtotal
            for tax in line.tax_id:
                price -= price * (1 - tax.amount)
            amount_dpp += price
        return round(amount_dpp, 2)
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.part.sales'].browse(docids)
        self.no = 0

        return {
            'doc_ids': docids,
            'doc_model': 'tw.part.sales',
            'docs': docs,
            'invoice': self.get_invoice,
            'payment_term': self.get_payment_term,
            'payment_term_date': self.get_payment_term_date,
            'time_date': self.time_date,
            'no_urut': self.no_urut,
            'terbilang': self.terbilang,
            'print_counter': self.print_counter,
            'dpp': self.get_dpp,
        }