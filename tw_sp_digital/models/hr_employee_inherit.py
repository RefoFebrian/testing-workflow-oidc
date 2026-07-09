# 1: imports of python lib
from datetime import date, datetime, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class EmployeeSpDigital(models.Model):
    _inherit = "hr.employee"

    # 7: defaults methods

    # 8: fields
    suspend_reason = fields.Char(string='Alasan Suspend')
    sp_level = fields.Selection(string='SP', selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
    ])
    evaluation_performance_level = fields.Selection(selection=[
        ('ep1', 'EP 1'),
        ('ep2', 'EP 2'),
        ('ep3', 'EP 3')
    ], string='Evaluation Performance Level')
    is_suspend = fields.Boolean(string='Akun disuspend')
    
    # Audit Trail
    suspend_date = fields.Datetime('Suspend on')
    suspend_uid = fields.Many2one('res.users', 'Suspend by')
    unsuspend_date = fields.Datetime('Unsuspend on')
    unsuspend_uid = fields.Many2one('res.users', 'Unsuspend by')

    # 9: relation fields
    sp_digital_ids = fields.One2many(comodel_name='tw.sp.digital', inverse_name='employee_id', string='Riwayat SP bulanan')
    line_ids = fields.One2many(comodel_name='tw.sp.digital.line', inverse_name='employee_id', string='Riwayat Detil SP')
    evaluation_performance_ids = fields.One2many(comodel_name='tw.employee.evaluation.performance', inverse_name='employee_id', string='Riwayat Performance')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def cron_calculate_evaluation_performance(self, datestr=None, params=None):
        master_calculate_ep_of_tl_obj = {
            'master_target_point_sales_partner': {'target': 5, 'point': 20},
            'master_target_cold_prospect': {'target': 625, 'point': 30},
            'master_target_volume_sales': {'target': 20, 'point': 50},
            'minimum_point_each_month': 50
        }
        master_calculate_ep_of_tl_obj = self.env['ir.config_parameter'].sudo().get_param('master.calculate.ep.of.tl')
        if master_calculate_ep_of_tl_obj:
            master_calculate_ep_of_tl_obj = eval(master_calculate_ep_of_tl_obj)
        minimum_point = int(master_calculate_ep_of_tl_obj.get('minimum_point_each_month'))
        if not datestr:
            datestr = date.today()
        else:
            datestr = parse(datestr).date()
        
        end = datestr.replace(day=1) - relativedelta(days=1)
        start = end.replace(day=1)

        # * if today is the first day of the the current month OR force execute is True
        # * Process data with last of MTD (eg. today is 2025-06-01, start = 2025-05-01 ; end = 2025-05-31)
        is_force_calculate = False
        if master_calculate_ep_of_tl_obj.get('is_force_execute'):
            is_force_calculate = master_calculate_ep_of_tl_obj.get('is_force_execute')
        if date.today().day == start.day or is_force_calculate:
            evaluation = self.env['tw.employee.evaluation.performance']
            domain = [('job_id.name','=','Team Leader Partner')]
            limit = 0
            if params:
                if params.get('limit'):
                    limit = params.get('limit')
                if params.get('list_of_emp_name'):
                    domain += [('name','in',params.get('list_of_emp_name'))]
            employees = self.sudo().search(domain, limit=limit)
            for emp in employees:
                self.env['tw.employee.incentive']._calculate_team_leader_incentive(emp, datestr)
                ep = evaluation.suspend_security().search([
                    ('employee_id','=',emp.id),
                    ('start_date','=',start.isoformat()),
                    ('end_date','=',end.isoformat())
                ], limit=1)
                
                if not ep:
                    ep = evaluation.suspend_security().create({
                        'employee_id': emp.id,
                        'start_date': start.isoformat(),
                        'end_date': end.isoformat()})

                try:
                    ep.calculate_evaluation_performance(end.isoformat(), target=minimum_point, master_calculate_ep_of_tl_obj=master_calculate_ep_of_tl_obj)
                    emp.evaluation_performance_ids = [4, ep.id]
                except Exception as err:
                    _logger.error(f'Cron Calculate Evaluation Performance Error:: {err}')

    def action_calculate_evaluation_performance(self):
        datestr = date.today()
        master_calculate_ep_of_tl_obj = {
            'master_target_point_sales_partner': {'target': 5, 'point': 20},
            'master_target_cold_prospect': {'target': 625, 'point': 30},
            'master_target_volume_sales': {'target': 20, 'point': 50},
            'minimum_point_each_month': 50
        }
        master_calculate_ep_of_tl_obj = self.env['ir.config_parameter'].sudo().get_param('master.calculate.ep.of.tl')
        if master_calculate_ep_of_tl_obj:
            master_calculate_ep_of_tl_obj = eval(master_calculate_ep_of_tl_obj)
        minimum_point = int(master_calculate_ep_of_tl_obj.get('minimum_point_each_month'))
        if master_calculate_ep_of_tl_obj.get('custom_date'):
            datestr = parse(master_calculate_ep_of_tl_obj.get('custom_date')).date()

        # * Process data with last of MTD (eg. today is 2025-06-01, start = 2025-05-01 ; end = 2025-05-31)
        end = datestr.replace(day=1) - relativedelta(days=1)
        start = end.replace(day=1)

        evaluation = self.env['tw.employee.evaluation.performance']
        ep = evaluation.suspend_security().search([
            ('employee_id','=',self.id),
            ('start_date','=',start.isoformat()),
            ('end_date','=',end.isoformat())
        ], limit=1)
        
        if not ep:
            ep = evaluation.suspend_security().create({
                'employee_id': self.id,
                'start_date': start.isoformat(),
                'end_date': end.isoformat()})

        ep.calculate_evaluation_performance(end.isoformat(), target=minimum_point, master_calculate_ep_of_tl_obj=master_calculate_ep_of_tl_obj)
        self.evaluation_performance_ids = [4, ep.id]

    def action_unsuspend_employee(self):
        self.suspend_security().write({
            'is_suspend': False,
            'suspend_reason': False,
            'unsuspend_date': datetime.now(),
            'unsuspend_uid': self._uid
        })

    # 14: private methods
    def _convert_config_parameter_from_scheduller(self, config_params):
        return eval(config_params)