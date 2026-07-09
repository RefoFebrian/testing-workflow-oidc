from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz


class PrintWorkOrderThermalInvoice(models.AbstractModel):
    _name = "report.tw_work_order.print_wo_thermal_invoice"
    _description = "Work Order Print Thermal Invoice"
    
    def doc_line(self, order_line):
        lines = [(i+1, line) for i, line in enumerate(order_line)]
        return lines
    
    def time_date(self):
        return datetime.now().strftime('%d-%m-%Y %H:%M')
    
    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name
    
    def print_user_role(self):
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return emp.job_id.name if emp else '-'
    
    def invoice_name(self):
        no_invoice = '-'
        move_obj = self.invoice_obj()
        if move_obj:
            no_invoice = move_obj.name

        return no_invoice
    
    def invoice_obj(self):
        work_order_obj = self.env['tw.work.order'].suspend_security().browse(self.env.context.get('active_ids', []))
        move_obj = self.env['account.move'].suspend_security().search([
            ('ref','ilike',work_order_obj.name),
            ('move_type','=','out_invoice')
        ], limit=1)

        return move_obj
    
    def harga_total_service(self):
        wo_obj = self.env['tw.work.order'].suspend_security().browse(self.env.context.get('active_ids', []))
        total = 0.0
        for line in wo_obj.order_line:
            if line.division == 'Service':
                total += line.price_subtotal

        return total
    
    def harga_total_sparepart(self):
        wo_obj = self.env['tw.work.order'].suspend_security().browse(self.env.context.get('active_ids', []))
        total = 0.0
        for line in wo_obj.order_line:
            if line.division == 'Sparepart':
                total += line.price_subtotal

        return total
    
    def get_dpp(self):
        wo_obj = self.env['tw.work.order'].suspend_security().browse(self.env.context.get('active_ids', []))
        dpp = wo_obj.amount_total or 0

        return dpp
    
    # def totals(self, amount):
    #     totalnya = fungsi_terbilang.terbilang(amount, 'idr', 'id')
        # return totalnya
        
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
    
    def print_vat(self, partner):
        return partner.vat or partner.no_npwp
    
    def print_counter(self):
        model_id = self.env.ref('tw_work_order.model_tw_work_order').id
        report_id = self.env.ref('tw_work_order.print_wo_invoice').id
        transaction_id = self.env.context.get('active_ids', [])[0]

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id','=',report_id),
            ('model_id','=',model_id),
            ('transaction_id','=',transaction_id)
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
        docs = self.env['tw.work.order'].sudo().browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.work.order',
            'docs': docs,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_user': self.print_user,
            'print_user_role': self.print_user_role,
            'invoice_obj': self.invoice_obj,
            'harga_total_service': self.harga_total_service,
            'harga_total_sparepart': self.harga_total_sparepart,
            'get_dpp': self.get_dpp,
            # 'totals': self.totals,
            'print_counter': self.print_counter,
            'print_address': self.print_address,
            'print_vat': self.print_vat
        }