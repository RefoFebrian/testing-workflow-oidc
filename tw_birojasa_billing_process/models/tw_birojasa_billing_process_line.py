from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwBirojasaBillingProcessLine(models.Model):
    _name = "tw.birojasa.billing.process.line"
    _description = "Tagihan Birojasa Line"

    name = fields.Char(related="lot_id.name", store=True)
    notice_number = fields.Char(string='Notice Number', required=False)
    notice_date = fields.Date(string='Notice Due Date', required=False)
    service_amount = fields.Float(string='Service', digits='Product Price')
    estimation_amount = fields.Float(string='Estimation Total', compute='_get_amount', compute_sudo=True, store=True, digits='Product Price')
    progressive_tax_amount = fields.Float(string='Progressive Tax', compute='_get_amount', compute_sudo=True, store=True, digits='Product Price')
    amount_total = fields.Float(string='Amount Total', required=True, digits='Product Price')
    correction_amount = fields.Float(string='Correction', compute='_get_amount', compute_sudo=True, store=True, digits='Product Price')
    doc_number = fields.Char(string='No Faktur STNK', related='lot_id.doc_number')
    vehicle_document_request_date = fields.Date(string='Request Date', related='lot_id.vehicle_document_request_date')
    vehicle_document_receive_date = fields.Date(string='Receive Date', related='lot_id.vehicle_document_receive_date')
    
    state = fields.Selection(related="lot_id.state", store=True)
    
    tax_ids = fields.Many2many('account.tax', related="birojasa_billing_id.tax_ids")
    customer_stnk_id = fields.Many2one(related="lot_id.customer_stnk_id", store=True)
    product_id = fields.Many2one(related="lot_id.product_id", store=True)
    city_id = fields.Many2one(related="lot_id.customer_stnk_id.city_id", store=True, string='City')
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Engine No', required=False, domain="[('registration_process_date', '!=', False), ('birojasa_billing_id', '=', False), ('company_id', '=', parent.company_id), ('biro_jasa_id', '=', parent.biro_jasa_id)]")
    birojasa_billing_id = fields.Many2one('tw.birojasa.billing.process', string="Tagihan Birojasa", ondelete='cascade')

    @api.constrains('amount_total', 'service_amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount_total <= 0:
                raise ValidationError(_("Amount Total must be greater than 0"))
            if rec.service_amount < 0:
                raise ValidationError(_("Service Amount must be greater than 0"))
                
    @api.depends('lot_id','amount_total')
    def _get_amount(self):
        for rec in self:
            estimation_amount = rec.lot_id.estimation_amount
            progressive_tax_amount = rec.lot_id.inv_progressive_tax_id.amount_total
            correction_amount = rec.amount_total - estimation_amount - progressive_tax_amount
            rec.estimation_amount = estimation_amount
            rec.progressive_tax_amount = progressive_tax_amount
            rec.correction_amount = correction_amount

    @api.onchange('lot_id')
    def onchange_lot(self):
        self.notice_number = False
        self.notice_date = False
        self.service_amount = False
        for record in self:
            if record.lot_id:
                record.notice_number = record.lot_id.notice_number
                record.notice_date = record.lot_id.notice_date
                record.service_amount = record.lot_id.service_amount

    def action_cancel(self):
        for rec in self:
            rec.lot_id.suspend_security().write({
                'birojasa_billing_id': False,
                'birojasa_billing_date': False,
            })