# 1: imports of python lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.exceptions import ValidationError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class EmployeeEvaluationPerformance(models.Model):
    _name = "tw.employee.evaluation.performance"
    _description = 'Evaluation Performance Employee'
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    is_achieve = fields.Boolean(string='Is Achieve?')
    minimum_point = fields.Integer(string='Minimum Point')
    total_point_result = fields.Integer(string='Total Point')

    # 9: relation fields
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    line_ids = fields.One2many(comodel_name='tw.employee.evaluation.performance.line', inverse_name='employee_ep_id', string='Detail Performance')

    # 10: constraints & sql constraints
    @api.constrains('line_ids')
    def _constraint_line_ids_point(self):
        for record in self:
            if sum([line.point for line in record.line_ids]) > 100:
                raise ValidationError('Total point tidak bisa melebihi 100!')

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def is_job(self, job_name):
        try:
            if self.employee_id.job_id.name.upper() == job_name.upper():
                return True
            return False
        except AttributeError as err:
            _logger.error(f'{", ".join(err.args)}')
            return False

    def get_subordinates(self):
        return self.env['hr.employee'].suspend_security().search([
            '|',
            ('parent_id','=',self.employee_id.id),
            ('coach_id','=',self.employee_id.id),
            ('working_end_date','=',False)
        ])

    def get_date_range(self, date_str):
        date_obj = parse(date_str)
        start = date_obj.replace(day=1)
        end = start + relativedelta(months=1, days=-1)

        return start.date().isoformat(), end.date().isoformat()

    def get_team_leader_sales_partner(self, master_calculate_ep_of_tl_obj=None):
        if self.is_job('TEAM LEADER PARTNER'):
            # * get dummy data if exist
            if master_calculate_ep_of_tl_obj.get('dummy_total_sales_partner'):
                return int(master_calculate_ep_of_tl_obj.get('dummy_total_sales_partner'))
            return len(self.get_subordinates())
        
        return 0

    def get_achieve_prospect(self, minat='cold', today=None, master_calculate_ep_of_tl_obj=None):
        if self.is_job('TEAM LEADER PARTNER'):
            start, end = self.get_date_range(today or date.today().isoformat())
            subordinate_ids = self.get_subordinates().ids
            # * get dummy data if exist
            if master_calculate_ep_of_tl_obj.get('dummy_total_cold_prospect'):
                return int(master_calculate_ep_of_tl_obj.get('dummy_total_cold_prospect'))
            leads = self.env['tw.lead'].suspend_security().search([
                ('minat','=',minat),
                ('employee_id','in',subordinate_ids),
                ('date','>=',start),
                ('date','<=',end)
            ])
            return len(leads)

        return 0

    def get_sales_volumes(self, today=None, master_calculate_ep_of_tl_obj=None):
        if self.is_job('TEAM LEADER PARTNER'):
            subordinate_ids = self.get_subordinates().ids
            start, end = self.get_date_range(today or date.today().isoformat())
            # * get dummy data if exist
            if master_calculate_ep_of_tl_obj.get('dummy_total_volume_sales'):
                return int(master_calculate_ep_of_tl_obj.get('dummy_total_volume_sales'))
            leads = self.env['tw.dealer.sale.order'].suspend_security().search([
                ('state','=','done'),
                ('employee_id','in',subordinate_ids),
                ('date','>=',start),
                ('date','<=',end)
            ])
            return len(leads)

        return 0

    def calculate_evaluation_performance(self, date_str, target=50, master_calculate_ep_of_tl_obj=None):
        start, end = self.get_date_range(date_str)
        master_sales_partner_of_tl = self._get_master_target_and_point_sales_partner_of_tl(master_calculate_ep_of_tl_obj)
        master_cold_prospect_of_tl = self._get_master_target_and_point_cold_prospect_of_tl(master_calculate_ep_of_tl_obj)
        master_volume_sales_of_tl = self._get_master_target_and_point_sales_volume_of_tl(master_calculate_ep_of_tl_obj)
        result_total_sales_partner_of_tl = self.get_team_leader_sales_partner(master_calculate_ep_of_tl_obj=master_calculate_ep_of_tl_obj)
        result_total_cold_prospect_of_tl = self.get_achieve_prospect(today=end, master_calculate_ep_of_tl_obj=master_calculate_ep_of_tl_obj)
        result_total_volume_sales_of_tl = self.get_sales_volumes(today=end, master_calculate_ep_of_tl_obj=master_calculate_ep_of_tl_obj)
        total_point_result = 0
        point_result_sales_partner_of_tl = 0
        if result_total_sales_partner_of_tl >= master_sales_partner_of_tl.get('target'):
            point_result_sales_partner_of_tl = master_sales_partner_of_tl.get('point')
            total_point_result += master_sales_partner_of_tl.get('point')
        point_result_cold_prospect_of_tl = 0
        if result_total_cold_prospect_of_tl >= master_cold_prospect_of_tl.get('target'):
            point_result_cold_prospect_of_tl = master_cold_prospect_of_tl.get('point')
            total_point_result += master_cold_prospect_of_tl.get('point')
        point_result_volume_sales_of_tl = 0
        if result_total_volume_sales_of_tl >= master_volume_sales_of_tl.get('target'):
            point_result_volume_sales_of_tl = master_volume_sales_of_tl.get('point')
            total_point_result += master_volume_sales_of_tl.get('point')
        line_ids = [
            [0, 0, {
                'name': 'Jumlah Salesman Partner / Bulan',
                'target': master_sales_partner_of_tl.get('target'),
                'point': master_sales_partner_of_tl.get('point'),
                'result': result_total_sales_partner_of_tl,
                'point_result': point_result_sales_partner_of_tl
            }],
            [0, 0, {
                'name': 'Jumlah Cold Prospect / Bulan',
                'target': master_cold_prospect_of_tl.get('target'),
                'point': master_cold_prospect_of_tl.get('point'),
                'result': result_total_cold_prospect_of_tl,
                'point_result': point_result_cold_prospect_of_tl
            }],
            [0, 0, {
                'name': 'Jumlah Volume Sales / Bulan',
                'target': master_volume_sales_of_tl.get('target'),
                'point': master_volume_sales_of_tl.get('point'),
                'result': result_total_volume_sales_of_tl,
                'point_result': point_result_volume_sales_of_tl
            }]
        ]

        self.line_ids = False
        ep = self.suspend_security().write({
            'name': f'Evaluation Performance periode {start} sampai {end}',
            'minimum_point': target,
            'total_point_result': total_point_result,
            'is_achieve': True if total_point_result >= target else False,
            'line_ids': line_ids,
        })

        if not self.is_achieve:
            # * check is current employee already got EP before or not (update or assign new EP 1)
            ep_level = 'ep1'
            vals = {'evaluation_performance_level': ep_level}
            if self.employee_id.evaluation_performance_level:
                if self.employee_id.evaluation_performance_level == 'ep1':
                    ep_level = 'ep2'
                else:
                    ep_level = 'ep3'
                    # * if EP Level already got until 3. suspend account for current employee team leader
                    vals.update({
                        'is_suspend': True,
                        'suspend_reason': 'Hasil dari Evaluation Performance sudah sampai EP3',
                        'suspend_date': datetime.now(),
                        'suspend_uid': self._uid
                    })
                vals.update({'evaluation_performance_level': ep_level})
            self.employee_id.suspend_security().write(vals)

    # 14: private methods
    def _get_master_target_and_point_sales_partner_of_tl(self, master_calculate_ep_of_tl_obj):
        master_target_point_sales_partner_obj = master_calculate_ep_of_tl_obj.get('master_target_point_sales_partner')
        return {'target': master_target_point_sales_partner_obj.get('target'), 'point': master_target_point_sales_partner_obj.get('point')}
    
    def _get_master_target_and_point_cold_prospect_of_tl(self, master_calculate_ep_of_tl_obj):
        master_target_cold_prospect_obj = master_calculate_ep_of_tl_obj.get('master_target_cold_prospect')
        return {'target': master_target_cold_prospect_obj.get('target'), 'point': master_target_cold_prospect_obj.get('point')}
    
    def _get_master_target_and_point_sales_volume_of_tl(self, master_calculate_ep_of_tl_obj):
        master_target_volume_sales_obj = master_calculate_ep_of_tl_obj.get('master_target_volume_sales')
        return {'target': master_target_volume_sales_obj.get('target'), 'point': master_target_volume_sales_obj.get('point')}