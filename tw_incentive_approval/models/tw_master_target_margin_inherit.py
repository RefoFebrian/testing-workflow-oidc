# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class MasterTargetMargin(models.Model):
    _name = "tw.master.target.margin"
    _inherit = ["tw.master.target.margin", "tw.approval.mixin"]

    # 7: defaults methods
    
    # 8: fields
    amount_total = fields.Float(default=1.0, string="Total Amount", help="A dummy field to trigger approval matrix")
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved', 'Approved'),
        ('active',),
        ('expired',),
        ('rejected',)
    ], string="Status")
    
    # 9: relation fields
    approval_ids = fields.One2many(
        comodel_name='tw.approval.line',
        inverse_name='transaction_id',
        string='Approval',
        domain=[('model_id', '=', _inherit)]
    )

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            existing_master = self.suspend_security().search([
                ('company_id', '=', vals['company_id']),
                ('job', '=', vals['job']),
                ('state', '=', 'active')
            ])
            if existing_master:
                target_margin_lines = vals.get('target_margin_line_ids', [])
                for line in target_margin_lines:
                    line_vals = line[2]
                    series_id = line_vals['series_id']

                    master_line = existing_master.target_margin_line_ids.filtered(lambda l: l.series_id.id == series_id)
                    if master_line.filtered(lambda l: l.cash > line_vals['cash'] or l.credit > line_vals['credit']):
                        vals['state'] = 'draft'
                        break
        
        return super(MasterTargetMargin,self).create(vals_list)

    # 13: action methods
    def action_request_approval(self):
        self.ensure_one()
        return super().action_request_approval(code='other')
    
    # 14: private methods
