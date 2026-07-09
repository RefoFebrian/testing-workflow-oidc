
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class ReportPaymentKlik(models.Model):
    _name = "tw.payment.klik"
    _description = "Payment Klik"
    
    def _get_default_company(self):
        return self.env.company.id

    name = fields.Char(string='Name',compute='_compute_name',store=True)
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
    ],default='draft',compute='_compute_state')
    
    company_id = fields.Many2one("res.company", string="Branch", required=True, default=_get_default_company)
    line_ids = fields.One2many(comodel_name='tw.payment.klik.line', inverse_name='payment_klik_id', string='Payments')
    

    @api.depends('company_id')
    def _compute_name(self):
        for item in self:
            item.name = self.env['ir.sequence'].get_sequence_code('AA', str(item.company_id.code))

    def _compute_state(self):
        for record in self:
            if all(line.state == 'done' for line in record.line_ids):
                record.state = 'done'
            elif any(line.state != 'draft' for line in record.line_ids):
                record.state = 'open'
            else:
                record.state = 'draft'
