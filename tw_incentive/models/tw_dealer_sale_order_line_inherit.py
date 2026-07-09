# -*- coding: utf-8 -*-

# 1: imports of python lib
import ast

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports
import logging

# 6: Import of unknown third party lib


class DealerSaleOrderLineInherit(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    # 7: defaults methods
    
    # 8: fields
    achieve_salesman_target = fields.Boolean()
    achieve_coordinator_target = fields.Boolean()
    incentive_state = fields.Selection(
        string='Incentive State',
        selection=[('draft', 'Draft'), ('done', 'Done'), ('skip', 'Skip'), ('error', 'Error')],
        default='draft')
    
    # 9: relation fields
    target_margin_sales_id = fields.Many2one(comodel_name='tw.master.target.margin.line')
    target_margin_coordinator_id = fields.Many2one(comodel_name='tw.master.target.margin.line')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def get_margin_values(self, salesman, job_type):
        """
        Compare the margin of the sale order line with the target margin.
        If the margin is greater than or equal to the target margin, set achieve_salesman_target to True.
        If the margin is less than the target margin, set achieve_salesman_target to False.
        """
        self.ensure_one()
        if not self.product_id.series_id:
            raise Warning(_(f"Product series is not defined for the product {self.product_id.name}."))
        
        margin_series = self.env['tw.master.target.margin.line'].sudo().search([
            ('target_margin_id.company_id', '=', self.order_id.company_id.id),
            ('target_margin_id.job', '=', job_type),
            ('target_margin_id.state', '=', 'active'),
            ('series_id.name', '=', self.product_id.series_id.name),
            ('year', '=', self.production_year)
        ], limit=1)
        if not margin_series:
            raise Warning(_(
                f"Master margin not found for product series '{self.product_id.series_id.name}'"
                f" in year '{self.production_year}' "
                f"with job position '{job_type.title()}'. Please ensure the master margin configuration exists for this combination.\n"
            ))
        
        net_margin = self.net_margin
        target_margin = margin_series.credit if self.order_id.finco_id else margin_series.cash

        return margin_series, net_margin, target_margin

    def check_margin(self):
        for line in self:
            margin_series, net_margin, target_margin = line.get_margin_values(line.salesman, line.job_type)
            if net_margin >= target_margin:
                line.achieve_salesman_target = True
            else:
                line.achieve_salesman_target = False

    # 14: private methods