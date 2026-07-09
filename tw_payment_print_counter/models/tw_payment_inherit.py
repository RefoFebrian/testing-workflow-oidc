# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError
class InheritAccountPayment(models.Model):
    _inherit = "tw.account.payment"

    cust_pay_kwitansi_line_id = fields.Many2one('tw.register.kwitansi.line', string="Nomor Kwitansi")

    def action_print_kwitansi(self):
        if self._context.get('from_print_wizard'):
            return super().action_print_kwitansi()

        report_id = self.env.ref('tw_payment.action_report_tw_payment_kwitansi').id
        print_count_obj = self.env['tw.print.counter'].search([
            ('model_id.model','=','tw.account.payment'),
            ('transaction_id','=',self.id),
            ('report_id','=',report_id),
        ])
        if not print_count_obj:
            print_count_obj = self.env['tw.print.counter'].create({
                'model_id': self.env.ref('tw_payment.model_tw_account_payment').id,
                'transaction_id': self.id,
                'report_id': report_id,
                'print_counter': 0,
            })

        return self.action_wizard_reason_for_reprinting(print_count_obj)

    def action_wizard_reason_for_reprinting(self, print_count_obj):
        form_id = self.env.ref('tw_payment_print_counter.tw_print_counter_reason_wizard_form_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Print Kwitansi',
            'view_mode': 'form',
            'target': 'new',
            # 'view_id': False,
            'res_model': 'tw.print.counter',
            # 'res_id': print_count_obj.id,
            'views': [(form_id, 'form')],
            'context':{'default_transaction_id': self.id, 'default_company_id': self.company_id.id, 'default_model_name':self._name, 'default_state':'open'},
        }