# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta
from pytz import timezone
from dateutil.relativedelta import relativedelta
import time
import os
from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning, ValidationError
import odoo.addons.decimal_precision as dp

class PeriodProfitBeforeTax(models.Model):
    _name = "tw.period.profit.before.tax"
    _description = "Period Profit Before Tax"

    @api.model
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return [company_ids[0].id]
        return False

    @api.depends('start_date', 'end_date')
    def _compute_period_time_formated(self):
        for record in self:
            start_date_formated = record.start_date.strftime("%d %b %Y")
            end_date_formated = record.end_date.strftime("%d %b %Y")
            record.period_time_formated = start_date_formated + " - " + end_date_formated

    name = fields.Char(required=True, string="Name", help="")
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    period_time_formated = fields.Char(string='Period', compute='_compute_period_time_formated', store=True)

    opex_avg = fields.Float('Opex AVG')
    total_unit_lm = fields.Float('Total Unit LM')
    total_net_margin_lm = fields.Float('Total Net Margin LM')
    refund_lm = fields.Float('Refund LM')
    pbt_propose_lm = fields.Float('PBT Propose LM')

    company_id = fields.Many2one('res.company', "Branch", default=_get_default_branch)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                branch = self.env['res.company'].browse(vals['company_id'])
                vals['name'] = self.env['ir.sequence'].get_sequence_code(branch.code, 'MPBT')

        return super().create(vals_list)

    def action_period_profit_before_tax_list(self):
        domain = False
        company_id = self.env['res.users'].suspend_security().browse(self._uid).company_ids.ids
        domain = [('company_id', 'in', company_id)]
        list_id = self.env.ref('tw_profit_before_tax.view_tw_period_profit_before_tax_list').id
        form_id = self.env.ref('tw_profit_before_tax.view_tw_period_profit_before_tax_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Period Profit Before Tax',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.period.profit.before.tax',
            'views': [(list_id, 'list'), (form_id, 'form')],
            'domain': domain,
            'context': {
                'readonly_by_pass': 1,
                'default_search_groupby_period_time_formated': 1,
                'group_by': ['period_time_formated']
            }
        }