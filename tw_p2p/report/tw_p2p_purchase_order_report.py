import datetime
import pytz
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class P2PPurchaseOrderReport(models.AbstractModel):
    _name = "report.tw_p2p.p2p_purchase_order_report"
    _description = "P2P Purchase Order Report"
    
    def doc_line(self, move_line):
        lines = [(i+1, line) for i, line in enumerate(move_line)]
        return lines
    
    def time_date(self, date):
        user = self.env.user
        now_utc = datetime.datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")
    
    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name
    
    def print_employee(self, user_id):
        return self.env['hr.employee'].suspend_security().search([('user_id','=',user_id)]).name
    
    def print_counter(self):
        model_id = self.env.ref('tw_p2p.model_tw_p2p_purchase_order').id
        report_id = self.env.ref('tw_p2p.action_report_p2p_purchase_order').id
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

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.p2p.purchase.order'].browse(docids)
        
        for doc in docs:
            if doc.state != 'confirmed':
                raise UserError(_('Print dapat dilakukan setelah State sudah Confirmed.'))
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.p2p.purchase.order',
            'docs': docs,
            'print_address': self.print_address,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_counter': self.print_counter,
            'print_user': self.print_user,
            'print_employee': self.print_employee,
        }