# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError as Warning

from datetime import datetime


class twMasterTargetMarginInherit(models.Model):
    _inherit = "tw.master.target.margin"

    net_margin_id = fields.Many2one(comodel_name='tw.profit.before.tax', string='PBT',
                                    help="Source target margin based on uploaded Net Margin")
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self._context.get('is_pbt'):
            records.action_request_approval()
            records.action_approval()
            records.action_confirm()
                
        return records
    
    def create_target_margin_from_pbt(self, pbt, job):
        
        line_ids = []
        for line in pbt.profit_before_tax_line_ids:
            if job == 'sales':
                cash = line.net_margin_salesman_cash / line.unit_cash_salesman if line.unit_cash_salesman else 0
                credit = line.net_margin_salesman_credit / line.unit_credit_salesman if line.unit_credit_salesman else 0
            
            elif job == 'sc':
                cash = line.net_margin_counter_cash / line.unit_cash_scounter if line.unit_cash_scounter else 0
                credit = line.net_margin_counter_credit / line.unit_credit_scounter if line.unit_credit_scounter else 0
                
            elif job == 'sco':
                cash = line.net_margin_sco_cash / line.unit_cash_sco if line.unit_cash_sco else 0
                credit = line.net_margin_sco_credit / line.unit_credit_sco if line.unit_credit_sco else 0
                
            line_ids.append(Command.create({
                'series_id': line.series_id.id,
                'year': line.year,
                'cash': cash,
                'credit': credit
            }))

        target_margin = self.with_context(is_pbt=True).create({
            'job': job,
            'company_id': pbt.company_id.id,
            'target_margin_line_ids': line_ids,
            'date': datetime.now(),
            'net_margin_id': pbt.id
        })

        target_margin._expire_previous_target(job, pbt.company_id)

        return target_margin
    
    def _expire_previous_target(self, job, branch):
        existing_target = self.search([('company_id', '=', branch.id),
                                       ('job', '=', job),
                                       ('id', '!=', self.id),
                                       ('state', '=', 'active')])
        
        if existing_target:
            existing_target.write({'state': 'expired'})
            