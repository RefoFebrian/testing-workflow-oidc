# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class InheritPrintCounter(models.Model):
    _inherit = "tw.print.counter"

    model_name = fields.Char(string='Model Name')
    receipt_print_count = fields.Integer(string='Receipt Print Count', compute='_compute_receipt_print_count')
    is_invisible = fields.Boolean(string='Show Reason', compute='_compute_is_invisible_reason')
    is_ekwitansi = fields.Boolean(string='Is E-Kwitansi')
    
    kwitansi_line_id = fields.Many2one('tw.register.kwitansi.line',string='Nomor Kwitansi')
    company_id = fields.Many2one('res.company', string="Branch",)
    transaction_id = fields.Integer(string='Transaction ID')

    @api.model
    def default_get(self, fields):
        res = super(InheritPrintCounter, self).default_get(fields)
        transaction_id = self.env.context.get('default_transaction_id')
        model_name = self.env.context.get('default_model_name')

        if transaction_id and model_name:
            model = self.env[model_name].browse(transaction_id)
            if model and model.cust_pay_kwitansi_line_id:
                res['kwitansi_line_id'] = model.cust_pay_kwitansi_line_id.id

        return res

    @api.onchange('is_ekwitansi')
    def _onchange_is_ekwitansi(self):
        if self.kwitansi_line_id:
            self.kwitansi_line_id = False

    @api.depends('transaction_id','model_name')
    def _compute_receipt_print_count(self):
        for rec in self:
            if rec.model_name and rec.transaction_id:
                model = self.env[rec.model_name].browse(rec.transaction_id)
                rec.receipt_print_count = getattr(model,'receipt_print_count',0)
            else:
                rec.receipt_print_count = 0
            
    @api.depends('receipt_print_count')
    def _compute_is_invisible_reason(self):
        for rec in self:
            if rec.receipt_print_count == 0:
                rec.is_invisible = False
            else:
                rec.is_invisible = True

    def action_print_kwitansi(self):
        model = self.env[self.model_name].browse(self.transaction_id)
        vals ={
            'transaction_id': self.transaction_id,
            'model_name': self.model_name,
            'state':'printed',
        }

        if self.model_name == 'tw.account.payment':
            vals['payment_id'] = model.id

        if self.reason:
            vals['reason'] = self.reason

        self.kwitansi_line_id.write(vals)

        model.cust_pay_kwitansi_line_id = self.kwitansi_line_id.id
        return model.with_context(from_print_wizard=True).action_print_kwitansi()