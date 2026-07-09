from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz


class PrintTravelDocumentStockPicking(models.AbstractModel):
    _name = "report.tw_stock.travel_document_template"
    _description = "Stock Picking Report Surat Jalan"
    
    def doc_line(self, move_line):
        lines = [(i+1, line) for i, line in enumerate(move_line)]
        return lines
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")
    
    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name
    
    # TODO: hidupkan jika sudah migrasi API Stock Distribution (PO dari DMS) 
    # def order_po(self):
    #     picking_obj = self.env['stock.picking'].suspend_security().browse(self.env.context.get('active_ids', []))
        
    #     order_po = False
    #     if picking_obj.origin[0:2] == 'MO':
    #         mutation_order_obj = self.env['wtc.mutation.order'].suspend_security().search([('name', '=', picking_obj.origin)])
    #         if mutation_order_obj:
    #             order_po = mutation_order_obj.dms_po_name
    #     return order_po
    
    def dealer_address(self):
        picking_obj = self.env['stock.picking'].suspend_security().browse(self.env.context.get('active_ids', []))
        dealer_name = ["", "", "", "", "", "", "", "", ""]
        if picking_obj.partner_id:
            dealer_name = [
                picking_obj.partner_id.name,
                picking_obj.partner_id.street,
                picking_obj.partner_id.rt,
                picking_obj.partner_id.rw,
                picking_obj.partner_id.sub_district_id.name,
                picking_obj.partner_id.district_id.name,
                picking_obj.partner_id.city_id.name,
                picking_obj.partner_id.state_id.name,
                picking_obj.partner_id.mobile
            ]
        return dealer_name
    
    def _get_invoice(self, picking):
        if hasattr(picking, 'sale_id') and picking.sale_id:
            invoices = picking.sale_id.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state != 'cancel'
            )
            if invoices:
                return invoices[0]
        
        if picking.origin:
            move_obj = self.env['account.move'].sudo().search([
                '|', ('invoice_origin', 'ilike', picking.origin), ('ref', 'ilike', picking.origin),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')
            ], limit=1)
            if move_obj:
                return move_obj
                
        return False

    def product_color(self, product):
        if not product:
            return False
        if isinstance(product, str):
            product = self.env['product.product'].sudo().search([('default_code', '=', product)], limit=1)
        if product:
            for ptav in product.product_template_variant_value_ids:
                if ptav.attribute_id.name and ptav.attribute_id.name.lower() in ('color', 'warna'):
                    return '%s - %s' % (ptav.product_attribute_value_id.code, ptav.product_attribute_value_id.name)
            for ptav in product.product_template_variant_value_ids:
                return '%s - %s' % (ptav.product_attribute_value_id.code, ptav.product_attribute_value_id.name)
        return False
    
    def print_counter(self):
        model_id = self.env.ref('tw_stock.model_stock_picking').id
        report_id = self.env.ref('tw_stock.travel_document_stock_picking_report').id
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
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_counter': self.print_counter,
            'dealer_address': self.dealer_address,
            
            'print_user': self.print_user,
            'product_color': self.product_color,
            '_get_invoice': self._get_invoice,
        }