from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TwWizardPrintKwitansi(models.TransientModel):
    _name = "tw.wizard.print.kwitansi"
    _description = "Wizard Pemilihan No Kwitansi"

    
    kwitansi_line_id = fields.Many2one(
        'tw.register.kwitansi.line',
        string='Nomor Kwitansi',
        required=True
    )
    receipt_print_count = fields.Integer(string='Receipt Print Count', compute='_compute_receipt_print_count')
    reason = fields.Char(string='Reason')
    transaction_id = fields.Integer(string='Transaction ID')
    model_name = fields.Char(string='Model Name')
    company_id = fields.Many2one('res.company', string="Branch",)
    is_invisible = fields.Boolean(string='Show Reason', compute='_compute_is_invisible_reason')

    @api.model
    def default_get(self, fields):
        res = super(TwWizardPrintKwitansi, self).default_get(fields)
        transaction_id = self.env.context.get('default_transaction_id')
        model_name = self.env.context.get('default_model_name')

        if transaction_id and model_name:
            model = self.env[model_name].browse(transaction_id)
            if model and model.register_kwitansi_line_id:
                res['kwitansi_line_id'] = model.register_kwitansi_line_id.id

        return res

    @api.depends('transaction_id','model_name')
    def _compute_receipt_print_count(self):
        for rec in self:
            if rec.model_name and rec.transaction_id:
                model = self.env[rec.model_name].browse(rec.transaction_id)
                rec.receipt_print_count = getattr(model,'receipt_print_count',0)
            
    @api.depends('receipt_print_count')
    def _compute_is_invisible_reason(self):
        for rec in self:
            if rec.receipt_print_count == 0:
                rec.is_invisible = False
            else:
                rec.is_invisible = True

    def action_print(self):
        self.ensure_one()
        model = self.env[self.model_name].browse(self.transaction_id)

        if not model:
            raise UserError("Print Gagal, Transaksi Tidak Ditemukan")

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

        model.register_kwitansi_line_id = self.kwitansi_line_id.id

        report_action = self.env.ref('tw_other_receivable.action_report_tw_other_receivable_report').report_action(model)
        report_action['close_on_report_download'] = True

        return report_action