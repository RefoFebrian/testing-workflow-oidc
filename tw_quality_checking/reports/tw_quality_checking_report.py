import datetime
import pytz
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class QualityCheckingReport(models.AbstractModel):
    _name = "report.tw_quality_checking.quality_checking_report"
    _description = "Quality Checking Report"
    
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
    
    def print_picking(self, transaction_line_obj):
        return ", ".join(transaction_line_obj.mapped("picking_id.name"))
    
    def print_counter(self):
        model_id = self.env.ref('tw_quality_checking.model_tw_quality_checking').id
        report_id = self.env.ref('tw_quality_checking.action_report_tw_quality_checking').id
        transaction_id = self.env.context.get('active_ids', [])[0]

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', transaction_id)
        ], limit=1)
        qc_obj = self.env['tw.quality.checking'].browse(transaction_id)

        if not print_obj:
            print_count_obj = self.env['tw.print.counter'].sudo().create({
                'model_id': model_id,
                'transaction_id': transaction_id,
                'print_counter': 1,
                'report_id': report_id
            })
            print_counter = print_count_obj.print_counter
        else:
            print_counter = print_obj.print_counter + 1
            print_obj.write({'print_counter': print_counter})
            
        qc_obj.write({'print_counter': qc_obj.print_counter + 1})
        return print_counter
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.quality.checking'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.quality.checking',
            'docs': docs,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_counter': self.print_counter,
            'print_user': self.print_user,
            'print_picking': self.print_picking,
            'print_employee': self.print_employee,
        }