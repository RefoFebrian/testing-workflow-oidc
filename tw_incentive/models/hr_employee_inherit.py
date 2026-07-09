# -*- coding: utf-8 -*-

# 1: imports of python lib
import traceback

# 2: import of known third party lib
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.tools import SQL

# 5: local imports
import logging

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)



class Employee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    # 7: defaults methods
    
    # 8: fields
    sales_category = fields.Selection(related='job_id.sales_category')
    total_subordinates = fields.Integer(string='Total Subordinates', compute='_compute_total_subordinates', help="Total number of subordinates under the employee")
    total_unit = fields.Integer(string='Total Unit', compute='_compute_monthly_total_unit', help="Total number of units sold by the employee in the current month")
    total_credit = fields.Integer(string='Total Credit', compute='_compute_monthly_total_credit', help="Total credit earned by the employee in the current month")
    total_mediator = fields.Integer(string='Total Mediator', compute='_compute_monthly_total_mediator', help="Total number of mediators handled by the employee in the current month")
    
    total_incentive = fields.Integer(string='Incentive Available', compute='_compute_total_incentive_monthly', help="Total incentive available for the employee in the current month")
    total_incentive_pending_in = fields.Integer(string='Incentive Pending In', compute='_compute_total_incentive_monthly', help="Total incentive pending to be received by the employee in the current month")
    total_incentive_pending_out = fields.Integer(string='Incentive Pending Out', compute='_compute_total_incentive_monthly', help="Total incentive pending to be paid out by the employee in the current month")
    total_earned = fields.Integer(string='Incentive Earned', compute='_compute_total_incentive_monthly', help="Total incentive earned by the employee in the current month")

    allowance_profession = fields.Float(string='Tunjangan Profesi', help="Allowance received based on the Provincial Minimum Wage (UMP)")
    allowance_trainee = fields.Float(string='Trainee Allowance', help="Allowance for employees with less than 3 months of service")
    incentive_sales = fields.Float(string='Sales Incentive', help="Incentive earned from sales performance")
    reward = fields.Float(string='Reward', help='Reward earned by the employee')

    # 9: relation fields
    incentive_ids = fields.One2many(comodel_name='tw.employee.incentive', inverse_name='employee_id', string='Incentive detail', help="")
    # evaluation_performance_ids = fields.One2many(comodel_name='tw.employee.evaluation.performance', inverse_name='employee_id')
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('incentive_ids')
    def _compute_total_subordinates(self):
        for record in self:
            record.total_subordinates = record._get_total_subordinates_by_sales()

    @api.depends('incentive_ids')
    def _compute_monthly_total_unit(self):
        for record in self:
            record.total_unit = record._get_total_unit()

    @api.depends('incentive_ids')
    def _compute_monthly_total_credit(self):
        for record in self:
            record.total_credit = record._get_total_unit('credit')

    @api.depends('incentive_ids')
    def _compute_monthly_total_mediator(self):
        for record in self:
            record.total_mediator = record._get_total_mediator()

    @api.depends('incentive_ids')
    def _compute_total_incentive_monthly(self):
        for record in self:
            incentives = self.get_employee_incentive()

            # Calculate values using ORM
            total_incentive = sum(i.incentive_available for i in incentives.filtered(lambda x: x.state == 'earned' and x.model_name == 'tw.dealer.sale.order'))
            pending_in_incentive = sum(i.incentive_available for i in incentives.filtered(lambda x: x.state == 'pending'))
            pending_out_incentive = sum(i.incentive_available for i in incentives.filtered(lambda x: x.model_name == 'tw.sp.digital'))
            earned_incentive = sum(i.incentive_value for i in incentives.filtered(lambda x: x.state == 'earned'))

            record.total_incentive = total_incentive
            record.total_incentive_pending_in = pending_in_incentive
            record.total_incentive_pending_out = pending_out_incentive
            record.total_earned = earned_incentive
    
    # 12: override methods
    
    # 13: action methods
    def calculate_incentive(self, sales_category, date_order, master_incentive, order_line=False):
        if sales_category in ('sales_payroll', 'sales_counter'):
            return self._calculate_incentive_payroll(date_order, master_incentive, order_line)
            
        elif sales_category == 'sales_partner':
            return self._calculate_incentive_partner(date_order, master_incentive, order_line)
        
        elif sales_category == 'sales_coordinator':
            return self._calculate_incentive_coordinator(date_order, master_incentive, order_line)
        
        elif sales_category == 'sales_team_leader':
            return self._calculate_incentive_team_leader(date_order)

        else:
            raise Warning(_(f"Invalid sales category: {sales_category}"))

    def get_employee_incentive(self, date_order=None):
        self.ensure_one()
        date_range = self._get_date_range(date_order)
        domain = [
            ('employee_id', '=', self.id),
            ('date', '>=', date_range['start']),
            ('date', '<=', date_range['end']),
        ]
        return self.env['tw.employee.incentive'].search(domain)
    
    def get_total_incentive(self, date_order=None):
        incentives = self.get_employee_incentive(date_order)
        return sum(i.incentive_available for i in incentives.filtered(lambda x: x.state in ('pending', 'earned') and x.model_name == 'tw.dealer.sale.order'))
    
    def get_total_incentive_details(self, name, date_order=None):
        incentives = self.get_employee_incentive(date_order)
        earned =incentives.filtered(lambda x: x.state == 'earned' and x.model_name == 'tw.dealer.sale.order')
        return earned.incentive_detail_ids.filtered(lambda x: x.name == name)
    
    def get_job_by_order_date(self, order_date):
        order_date = datetime.combine(order_date, datetime.min.time())
        record = self.env['tw.employee.career.record'].get_career_record_by_date(self.id, order_date)
        return record.get_current_model_record() if record else self.job_id
    
    # 14: private methods
    def _get_total_subordinates_by_sales(self, date=None, excludes=None):
        self.ensure_one()
        domain = [
            ('incentive_state', '=', 'done'),
            ('sales_coordinator_id', '=', self.id)
        ]
        if date:
            domain += self._get_domain_dealer_sale_order(date)
        if excludes:
            domain.append(('id', '!=', excludes))

        orders = self.env['tw.dealer.sale.order'].search(domain)
        # Use set comprehension for unique sales_id, filter out False in one step
        active_salesmen = set(orders.mapped('sales_id')).difference([False])
        return len(active_salesmen)
    
    def _get_total_unit(self, payment_type=None, date=None, excludes=None):
        self.ensure_one()
        domain = []
        domain += self._get_domain_dealer_sale_order(date)

        if payment_type == 'cash':
            domain.append(('finco_id', '=', False))        
        elif payment_type == 'credit':
            domain.append(('finco_id', '!=', False))

        if excludes:
            domain.append(('id', '!=', excludes))

        orders = self.env['tw.dealer.sale.order'].sudo().search(domain)
        order_line = orders.order_line.filtered(lambda x: x.incentive_state == 'done' and x.id != excludes)
        return len(order_line)
    
    def _get_total_mediator(self, payment_type=None, date=None):
        self.ensure_one()
        sales_id = 'sales_coordinator_id' if self.sales_category == 'sales_coordinator' else 'sales_id' 
        domain = [(sales_id, '=', self.id)]
        if payment_type == 'credit':
            domain.append(('finco_id', '!=', False))
        elif payment_type == 'cash':
            domain.append(('finco_id', '=', False))

        domain += self._get_domain_dealer_sale_order(date)
        achieve_target = 'achieve_coordinator_target' if self.sales_category == 'sales_coordinator' else 'achieve_salesman_target' 
        orders = self.env['tw.dealer.sale.order'].sudo().search(domain)
        order_line = orders.order_line.filtered(lambda x: not getattr(x, achieve_target) and x.incentive_state == 'done')
        return len(order_line)

    def _get_job_date_domain(self, date_order):
        job = self.job_id if not date_order else self.get_job_by_order_date(date_order)
        if not date_order:
            date_range = self._get_date_range(None)
            start = date_range['start']
            end = date_range['end']
        else:
            start = date_order.replace(day=1)
            end = date_order
        return job, start, end

    def _get_domain_dealer_sale_order(self, order_date=False):
        job, start, end = self._get_job_date_domain(order_date)
        job_category = job.sales_category
        job_id = 'sales_coordinator_id' if job_category == 'sales_coordinator' else 'sales_id'
        return [
            (job_id, '=', self.id),
            ('state','in', ('sale', 'done')),
            ('date_order', '>=', start),
            ('date_order', '<=', end)
        ]

    def _get_date_range(self, date_order=None):
        date = date_order or (datetime.now() + timedelta(hours=7))
        start_date = datetime(date.year, date.month, 1).date()
        end_date = (start_date + relativedelta(months=1, days=-1)) if not date_order else date
        return {'start': start_date, 'end': end_date}

    def _get_incentive_requirement(self, date_order):
        total_unit_sales = self._get_total_unit(date=date_order)
        total_credit_sales = self._get_total_unit(payment_type='credit', date=date_order)
        total_cash_sales = total_unit_sales - total_credit_sales
        mediator_credit_count = self._get_total_mediator(payment_type='credit', date=date_order)
        mediator_cash_count = self._get_total_mediator(payment_type='cash', date=date_order)
        mediator_count = mediator_credit_count + mediator_cash_count
        non_mediator_count = total_unit_sales - mediator_credit_count - mediator_cash_count

        return {
            'total_unit': total_unit_sales,
            'total_credit': total_credit_sales,
            'total_cash': total_cash_sales,
            'total_prev_unit': total_unit_sales - (1 if total_unit_sales > 0 else 0),
            'total_prev_credit': total_credit_sales - (1 if total_credit_sales > 0 else 0),
            'total_prev_cash': total_cash_sales - (1 if total_cash_sales > 0 else 0),
            'mediator_unit': mediator_count,
            'mediator_credit': mediator_credit_count,
            'mediator_cash': mediator_cash_count,
            'non_mediator': non_mediator_count,
            'mediator_prev_unit': mediator_count - (1 if mediator_count > 0 else 0),
            'mediator_prev_credit': mediator_credit_count - (1 if mediator_credit_count > 0 else 0),
            'mediator_prev_cash': mediator_cash_count - (1 if mediator_cash_count > 0 else 0),
            'non_prev_mediator': non_mediator_count - (1 if non_mediator_count > 0 else 0),
        }
    
    def _calculate_incentive_payroll(self, date_order, master_incentive, order_line=False):
        self.ensure_one()
        emp_incentive = self.env['tw.employee.incentive']
        incentive_sales = incentive_credit = incentive_reward = incentive_amount = 0
        
        # Initialize variables for calculation
        req = self._get_incentive_requirement(date_order)
        
        incentive = master_incentive.get_incentive_line(req['total_unit'])
        prev_incentive = master_incentive.get_incentive_line(req['total_prev_unit'])

        if order_line.order_id.finco_id:
            incentive_credit = (incentive.credit * (req['total_credit'] - req.pop('mediator_credit')))
            total_credit_count = emp_incentive.get_previous_incetive_detail(self.id, 'Total Credit')
            mediator_credit_count = emp_incentive.get_previous_incetive_detail(self.id, 'Mediator Credit')
            prev_incentive_credit = (prev_incentive.credit * (total_credit_count - mediator_credit_count))
            incentive_credit -= prev_incentive_credit
            incentive_amount += incentive_credit
        else:
            incentive_sales = (incentive.cash * (req['total_cash'] - req.pop('mediator_cash')))
            total_cash_count = emp_incentive.get_previous_incetive_detail(self.id, 'Total Cash')
            mediator_cash_count = emp_incentive.get_previous_incetive_detail(self.id, 'Mediator Cash')
            prev_incentive_cash = (prev_incentive.cash * (total_cash_count - mediator_cash_count))
            incentive_sales -= prev_incentive_cash
            incentive_amount += incentive_sales
        
        # Counter tidak mendapatkan Reward
        if self.sales_category == 'sales_payroll':
            incentive_reward = incentive.reward - prev_incentive.reward
            incentive_amount += incentive_reward
        
        req.update({
            'incentive_cash': incentive_sales,
            'incentive_credit': incentive_credit,
            'incentive_reward': incentive_reward,
            'incentive': incentive_amount
        })
        return req
    
    def _calculate_incentive_partner(self, date_order, master_incentive, order_line=False):
        self.ensure_one()
        incentive_sales = incentive_credit = incentive_reward = incentive = 0
        
        # Initialize variables for calculation
        req = self._get_incentive_requirement(date_order)

        incentive = master_incentive.get_incentive_line(req['total_unit'])
        prev_incentive = master_incentive.get_incentive_line(req['total_prev_unit'])
        credit_incentive = master_incentive.get_incentive_line(req['total_credit'])

        percentage_precense = 1
        is_credit = 1 if order_line.order_id.finco_id else 0
        is_mediator = 1 if not order_line.achieve_salesman_target else 0
        
        total_unit_sales = req['total_unit'] or 1
        percentage_credit = req['total_credit'] / total_unit_sales
        percentage_mediator = req['mediator_unit'] / total_unit_sales

        total_prev_sales = req.get('total_prev_unit', 0) or 1
        percentage_prev_credit = (req['total_credit'] - is_credit) / total_prev_sales
        percentage_prev_mediator = (req['mediator_unit'] - is_mediator) / total_prev_sales

        reward = ((incentive.reward * percentage_credit) - ((incentive.reward * percentage_credit) * percentage_mediator)) * percentage_precense
        prev_reward = ((prev_incentive.reward * percentage_prev_credit) - ((prev_incentive.reward * percentage_prev_credit) * percentage_prev_mediator)) * percentage_precense

        incentive_sales = incentive.cash
        incentive_credit = credit_incentive.credit if is_credit else 0
        incentive_reward = reward - prev_reward
        
        incentive = incentive_sales + incentive_credit + incentive_reward

        req.update({
            'incentive_sales': incentive_sales,
            'incentive_credit': incentive_credit,
            'incentive_reward': incentive_reward,
            'incentive': incentive
        })

        return req
    
    def _calculate_incentive_coordinator(self, date_order, master_incentive, order_line=False):
        self.ensure_one()
        incentive_sales = incentive_credit = incentive_reward = incentive = 0
        
        # Initialize variables for calculation
        req = self._get_incentive_requirement(date_order)
        total_unit_sales = req['total_unit']
        mediator_credit_count = req.pop('mediator_credit')
        mediator_cash_count = req.pop('mediator_cash')

        non_mediator_count = total_unit_sales - mediator_credit_count - mediator_cash_count
        total_credit_sales = req['total_credit'] - mediator_credit_count

        incentive = master_incentive.get_incentive_line(total_unit_sales)

        incentive_non_mediator = master_incentive.get_incentive_line(non_mediator_count)
        credit_incentive_non_mediator = master_incentive.get_incentive_line((total_credit_sales))

        percentage_reward = 0
        percentage_precense = 1
        
        # Reward
        subordinates = self._get_total_subordinates_by_sales(date_order) or 1
        if subordinates >= 10:
            percentage_reward += 0.5

        productivity = round(self._get_total_unit(date=date_order) / subordinates)
        if productivity >= 8:
            percentage_reward += 0.5

        reward = (incentive.reward * percentage_reward) * percentage_precense
    
        new_incentive = incentive_non_mediator.accumulate_cash + credit_incentive_non_mediator.accumulate_credit + reward
        existing_incentive = self.get_total_incentive(date_order)

        incentive_sales = incentive_non_mediator.cash
        incentive_credit = credit_incentive_non_mediator.credit
        incentive_reward = reward
        # format incentive value to a monetary-like format use {[value]:,.2f}
        # additional_remarks += f"/ Incentive : {new_incentive:,.2f}"
        # FINAL
        incentive = new_incentive - existing_incentive

        req.update({
            'subordinates': subordinates,
            'productivity': productivity,
            'incentive_sales': incentive_sales,
            'incentive_credit': incentive_credit,
            'incentive_reward': incentive_reward,
            'incentive': incentive
        })

        return req
    
    def _calculate_incentive_team_leader(self, order_date=None):
        self.ensure_one()

        incentive = {
            'allowance_profession': self.allowance_profession,
        }
        incentive.update(self._get_trainee_allowance(order_date))
        incentive.update(self._get_incentive_team_leader(order_date))
        incentive.update(self._get_reward_team_leader(order_date))
        incentive['incentive'] = (incentive.get('allowance_profession', 0) + incentive.get('nominated', 0) + incentive.get('incentive_team_leader', 0) + incentive.get('reward_team_leader', 0))
        return incentive

    def _get_trainee_allowance(self, trx_date=False, prev=False):
        date = self._get_date_range(trx_date)
        today = date.get('end')
        today = today.date() if isinstance(today, datetime) else today

        trainees = []
        for emp in self.child_ids:
            # check trainee who has less than 3 months working days
            if (today - emp.working_start_date).days <= (today - (today - relativedelta(months=3))).days:
                trainees.append(emp)

        if len(trainees) >= 5:
            # allowance is given if trainee under TL is gte 5 and max is 8
            nominated_trainees = self._calculate_trainee_prospect(trainees, trx_date=trx_date, prev=prev)
            if nominated_trainees:
                nominated = nominated_trainees['nominated']
                nominated_trainees.update({
                    'nominated': (nominated * 100000) - ((nominated - 1) * 100000 * 0.1)
                })
                return nominated_trainees

        return {}
    
    def _get_incentive_team_leader(self, trx_date=False, prev=False):
        date = self._get_date_range(trx_date)
        incentive_tl = {}
        
        search_params = [('date_order', '>=', date.get('start')),
                            ('date_order', '<=', date.get('end')),
                            ('sales_coordinator_id', '=', self.id)]
        if prev:
            search_params.append(('id', '!=', prev))

        sales = self.env['tw.dealer.sale.order'].search(search_params)
        sales_count = sum([line.product_uom_qty for order in sales for line in order.order_line])
        if not sales_count:
            return incentive_tl
        
        prev_sales = sales_count - 1
        incentive = sales_count * (20000 if sales_count >= 20 else 15000)
        prev_incentive = prev_sales * (20000 if prev_sales >= 20 else 15000)
        incentive_tl['sales_count'] = sales_count
        incentive_tl['prev_sales'] = prev_sales
        incentive_tl['incentive_team_leader'] = incentive - prev_incentive
            
        return incentive_tl

    def _get_reward_team_leader(self, trx_date=False, prev=False):
        date = self._get_date_range(trx_date)
        reward_tl = {}
        search_params = [('date_order', '>=', date.get('start')),
                            ('date_order', '<=', date.get('end')),
                            ('sales_coordinator_id', '=', self.id)]
        if prev:
            search_params.append(('id', '!=', prev))
            
        sales = self.env['tw.dealer.sale.order'].search(search_params)
        sales_count = sum([line.product_uom_qty for order in sales for line in order.order_line])
        if sales_count < 10:
            return reward_tl
        
        curr = self._calculate_tl_reward(sales_count)
        prev = self._calculate_tl_reward(sales_count - 1)

        reward_tl['sales_count'] = sales_count
        reward_tl['prev_sales'] = sales_count - 1
        reward_tl['reward_team_leader'] = curr - prev

        return reward_tl
        
    def _calculate_tl_reward(self, unit_sold):
        if unit_sold >= 50:
            return 3200000
        elif unit_sold >= 40:
            return 2500000
        elif unit_sold >= 30:
            return 2000000
        elif unit_sold >= 20:
            return 800000
        elif unit_sold >= 10:
            return 250000
        else:
            return 0
    
    def _get_all_incentive_values(self, model, type, trx_date, remarks, amount):
        values = []
        date = self._get_date_range(trx_date)
        emp_incentive = self.env['tw.employee.incentive']
        ir_model = self.env['ir.model'].search([('model', '=', model)])
        incentive = emp_incentive.search([
            ('company_id', '=', self.company_id.id),
            ('type', '=', type),
            ('date', '>=', date.get('start')),
            ('date', '<=', date.get('end')),
            ('state', '=', 'earned'),
            ('model_name', '=', ir_model.model),
            ('model_id', '=', ir_model.id),
            ('employee_id', '=', self.id)], limit=1)
        if not incentive:
            values = [0, 0, {
                'company_id':  self.company_id.id,
                'type': type,
                'date': trx_date,
                'state': 'earned',
                'model_name': ir_model.model,
                'employee_id': self.id,
                'model_id': ir_model.id,
                'incentive_value': amount,
                'remarks': remarks
            }]
        else:
            values = [1, incentive.id, {
                'type': type,
                'date': trx_date,
                'incentive_value': amount,
                'remarks': remarks
            }]
        
        return values
    
    def _calculate_trainee_prospect(self, trainees, trx_date=None, prev=None):
        date = self._get_date_range(trx_date)
        trx_date = trx_date.date() if isinstance(trx_date, datetime) else trx_date
        start_date = date.get('start')
        end_date = date.get('end')
        tot_cold = tot_hot = tot_do = nominated = 0
        
        for emp in trainees:
            domain = []
            if prev:
                domain.append(('id', '!=', prev))

            leads = self.env['tw.lead'].search(domain + [
                ('sales_id', '=', emp.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date)])
            
            dsos = self.env['tw.dealer.sale.order'].search(domain + [
                ('sales_id', '>=', emp.id),
                ('date_order', '>=', start_date),
                ('date_order', '<=', end_date)])

            cold = sum([1 for lead in leads if lead.interest == 'cold'])
            hot = sum([1 for lead in leads if lead.interest == 'hot'])
            do = len(dsos)
            
            days = (trx_date - emp.working_start_date).days
            if days >= 60 and (cold >= 125 and hot >= 25 and do >= 3):
                nominated += 1
            elif days >= 30 and (cold >= 125 and hot >= 25 and do >= 2):
                nominated += 1
            elif cold >= 125:
                nominated += 1
            
            tot_cold += cold
            tot_hot += hot
            tot_do += do
            
            if nominated == 8:
                break
        
        return {
            'total_cold': tot_cold,
            'total_hot': tot_hot,
            'total_do': tot_do,
            'nominated': nominated
        }

