# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api


class ProfitBeforeTax(models.Model):
    _name = "tw.profit.before.tax"
    _inherit = ["tw.profit.before.tax", "tw.approval.mixin"]

    # 8: fields
    amount_total = fields.Float(compute='_compute_amount_total')
    state = fields.Selection(selection_add=[
        ('draft'),
        ('waiting_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('confirmed'),
        ('rejected')
    ])
   
    # Audit Trail
    approve_date = fields.Datetime(string='Approved on')
    approve_uid = fields.Many2one(comodel_name='res.users', string='Approved by')
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('profit_before_tax_line_ids.state')
    def _compute_amount_total(self):
        for record in self:
            if record.profit_before_tax_line_ids.filtered(lambda x: x.state != 'approved'):
                record.amount_total = 0
            else:
                record.amount_total = 1

    # 12: override methods
    
    # 13: action methods
    def get_total_value(self):
        total = 0
        for line in self.petty_cash_out_ids:
            total = total + line.amount
        return total

    def get_rfa_additional_vals(self):
        self.ensure_one()
        return {
            'state': 'waiting_for_approval',
        }

    def get_approve_additional_vals(self):
        self.ensure_one()
        return {
            'confirm_uid': self._uid,
            'confirm_date': datetime.now(),
            'state': 'approved'
        }

    def action_approval(self):
        approval_status = super().action_approval()
        if approval_status == 1:
            self.action_confirm()
        return approval_status

    def _get_default_date(self):
        return datetime.now()
    