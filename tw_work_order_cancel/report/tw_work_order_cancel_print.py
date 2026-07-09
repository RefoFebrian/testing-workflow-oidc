from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz


class PrintWorkOrderCancelPrint(models.AbstractModel):
    _name = "report.tw_work_order_cancel.tw_work_order_cancel_print"
    _description = "Work Order Cancel Print"
    
    def doc_line(self, order_line):
        lines = [(i+1, line) for i, line in enumerate(order_line)]
        return lines
    
    def time_date(self):
        return datetime.now().strftime("%d-%m-%Y %H:%M")
    
    def only_date(self):
        return datetime.now().strftime("%d-%m-%Y")
    
    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name
    
    def dealer_address(self):
        work_order_cancel_obj = self.env['tw.work.order.cancel'].suspend_security().browse(self.env.context.get('active_ids', []))
        dealer_name = ["", "", "", "", "", "", "", "", ""]
        if work_order_cancel_obj.partner_id:
            dealer_name = [
                work_order_cancel_obj.partner_id.name,
                work_order_cancel_obj.partner_id.street,
                work_order_cancel_obj.partner_id.rt,
                work_order_cancel_obj.partner_id.rw,
                work_order_cancel_obj.partner_id.sub_district_id.name,
                work_order_cancel_obj.partner_id.district_id.name,
                work_order_cancel_obj.partner_id.city_id.name,
                work_order_cancel_obj.partner_id.state_id.name,
                work_order_cancel_obj.partner_id.mobile
            ]
        return dealer_name
    
    def invoice_name(self):
        no_invoice = "-"
        work_order_cancel_obj = self.env['tw.work.order.cancel'].suspend_security().browse(self.env.context.get('active_ids', []))
        move_obj = self.env['account.move'].suspend_security().search([
            ('ref', 'ilike', work_order_cancel_obj.name), 
            ('move_type', '=', 'out_invoice')], limit=1)
        if move_obj:
            no_invoice = move_obj.name
        return no_invoice
    
    # def product_color(self,code):
    #     query = f"""
    #         SELECT attr_value.name
    #             FROM product_product product
    #             LEFT JOIN product_variant_combination variant ON product.id = variant.product_product_id
    #             LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
    #             LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
    #         WHERE product.default_code = '{code}'
    #     """
    #     self._cr.execute(query)
    #     data = self._cr.fetchone()
    #     if data:
    #         return data[0]
        
    #     return False
    
    def print_counter(self):
        model_id = self.env.ref('tw_work_order_cancel.model_tw_work_order_cancel').id
        report_id = self.env.ref('tw_work_order_cancel.tw_work_order_cancel_print').id
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
        
        docs = self.env['tw.work.order.cancel'].browse(docids)
        user = self.env['res.users'].browse(self._uid).name
        # tgl = datetime.strptime(self.create_date,'%Y-%m-%d')
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.work.order.cancel',
            'docs': docs,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_counter': self.print_counter,

            'today':str(datetime.now()),
            'user': user,
            'company_id': '['+str(docs.company_id.code)+'] '+str(docs.company_id.name),
            'division': str(docs.division),
            'date': str(docs.date),
            'wo':str(docs.name),
            'reason':docs.reason,

            # 'dealer_address': self.dealer_address,
            # 'invoice_name': self.invoice_name,
            # 'print_user': self.print_user,
            # 'product_color': self.product_color
        }