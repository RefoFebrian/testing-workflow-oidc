# -*- coding: utf-8 -*-

# 1: imports of python lib
import ast

# 2: import of known third party lib
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.tools import SQL

# 5: local imports
import logging
import calendar

# 6: Import of unknown third party lib


class RecalculateIncentive(models.Model):
    _name = "tw.recalculate.incentive"
    _description = "Recalculate Incentive"
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now() + timedelta(hours=7)

    # 8: fields
    name = fields.Char(string='Name')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date', default=_get_default_date)
    date = fields.Date(string='Date',default=_get_default_date)
    state = fields.Selection(string='State', selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'),],default='draft')
    month = fields.Selection(
        [(str(idx), str(calendar.month_name[idx])) for idx in range(1, 13)],
        string='Month',
        default=str((datetime.now() + timedelta(hours=7) - relativedelta(months=1)).month)
    )
    year = fields.Selection(
        [(str(num), str(num)) for num in range(2010, (datetime.now().year)+1)],
        string='Year',
        default=str((datetime.now() + timedelta(hours=7) - relativedelta(months=1)).year)
    )
    reason = fields.Text()
    
    total_data = fields.Integer(string='Total Data')
    remaining_data = fields.Integer(string='Remaining Data')
    percentage_remaining_data = fields.Float(default=0)

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', 'Confirmed By')
    confirm_date = fields.Datetime('Confirmed On')
	
    # 9: relation fields 
    company_id = fields.Many2one(comodel_name='res.company', string='Branch')
    incentive_ids = fields.One2many(comodel_name='tw.employee.incentive', inverse_name='recalculate_id')

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.onchange('start_date')
    def onchange_start_date(self):
        start_date = self.start_date
        if start_date:
            today = date.today()
            year = start_date.year
            month = start_date.month
            day = calendar.monthrange(year, month)[1]
            if [today.month, today.year] != [month, year]:
                self.end_date = self.date = date(year=year, month=month, day=day)
            else:
                self.end_date = self.date = today
            self.month = str(month)
            self.year = str(year)
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company = self.env['res.company'].browse(vals.get('company_id'))
            ref = self.env['ir.sequence'].get_sequence_code('RCI', company.code)
            vals['name'] = ref            
        recalculate = super(RecalculateIncentive, self).create(vals_list)
        return recalculate

    # 13: action methods
    def action_confirm_without_date_check(self):
        self.action_confirm(date_check=False)

    def action_confirm(self, date_check=True):
        today = self._get_default_date().date()
        last_month = (today - relativedelta(months=1))
        
        if self.start_date:
            last_month = self.start_date

        # Date validation
        if date_check:
            # Check if confirming an old transaction
            if str(self.month) != str(last_month.month) or str(self.year) != str(last_month.year):
                raise Warning(_(f"You can only confirm transactions for the month and year of {last_month.month} {last_month.year}!"))
            # Check: cannot be after the 2nd day
            recalculate_day_limit = self.env['ir.config_parameter'].sudo().get_param('tw_incentive.recalculate_day_limit') or 2
            if today.day > int(recalculate_day_limit):
                raise Warning(_(f"Recalculation can only be done until the {recalculate_day_limit}th of each month!"))

        # Check if there are still DSO data that have not been calculated
        outstanding_dso_check = self._get_outstanding_dso()
        if outstanding_dso_check:
            raise Warning(_(f"There are still {len(outstanding_dso_check)} data being calculated, please wait a moment"))

        # fomonth = today.replace(day=1).replace(month=int(self.month))
        fomonth = self.start_date

        self._cr.execute(SQL("""
            UPDATE tw_dealer_sale_order 
            SET incentive_state = 'draft'
                , error_message = null 
                , incentive_retry_count = 0
            WHERE incentive_state = 'done'
                AND company_id = %s
                AND (date_order + INTERVAL '7 hours')::DATE BETWEEN %s AND %s
            RETURNING id, name
        """, self.company_id.id, self.start_date, self.end_date))
        dso_result = self._cr.fetchall()
        if not dso_result:
            raise Warning(f"Dealer Sale Order {self.company_id.name} period {self.start_date} - {self.end_date} not found!")
        
        dso_ids = tuple([res[0] for res in dso_result])
        dso_name = tuple([res[1] for res in dso_result])

        self._cr.execute("""
            UPDATE tw_dealer_sale_order_line 
            SET incentive_state = 'draft'
                , achieve_coordinator_target = null
                , achieve_salesman_target = null
                , target_margin_coordinator_id = null
                , target_margin_sales_id = null 
            WHERE incentive_state = 'done' 
                AND order_id IN %s 
        """, (dso_ids,))

        self._cr.execute("""
            UPDATE tw_employee_incentive 
            SET state = 'cancelled'
            WHERE model_name = 'tw.dealer.sale.order'
            AND recalculate_id IS NULL
            AND state != 'cancelled'
            AND transaction_ref IN %s
            RETURNING id
        """, (dso_name,))
        result = self._cr.fetchall()

        if result:
            self._cr.execute("""
                UPDATE tw_employee_incentive
                SET recalculate_id = %s
                WHERE id IN %s
            """, (self.id, tuple([res[0] for res in result])))

            for res in result:
                self.env['tw.employee.incentive.history'].suspend_security().create({
                    'date': date.today(),
                    'description': f'Recalculated by {self.name}',
                    'type': 'redeem',
                    'state': 'rejected',
                    'reject_date': date.today(),
                    'alasan_reject': self.reason,
                    'employee_incentive_id': res[0],
                })

        total_data = len(self._get_outstanding_dso())
        state = 'confirmed'
        if total_data == 0:
            state = 'done'

        self.suspend_security().write({
            'confirm_date': self._get_default_date(),  
            'confirm_uid': self._uid,
            'state': state,
            'total_data': total_data,
            'remaining_data': total_data,
        })
        self.action_check_outstanding_calculation()

    def action_check_outstanding_calculation(self):
        if self.remaining_data != 0:
            remaining_data = len(self._get_outstanding_dso(self.confirm_date))
            
            total_outstanding = self.total_data - remaining_data
            total = float(total_outstanding) / float(self.total_data or 1)

            vals = {
                'remaining_data':remaining_data,
                'percentage_remaining_data':total*100
                }
            if remaining_data == 0:
                vals['state'] = 'done'
            self.write(vals)
        elif self.total_data == 0:
            self.write({
                'percentage_remaining_data':100
            })

    def schedulled_check_outstanding_calculation(self):
        to_check = self.sudo().search([('remaining_data','!=',0)])
        for data in to_check:
            data.action_check_outstanding_calculation()

    def _get_outstanding_dso(self,end_date=False):
        filters = [
            ('incentive_state', '=', 'draft'),
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ['sale','done'])
        ]
        if end_date:
            filters.append(('date_order', '<=', end_date))

        outstanding_dso = self.env['tw.dealer.sale.order'].suspend_security().search(filters)
        return outstanding_dso
