# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWBoomDelegationTask(models.TransientModel):
    _name = "tw.boom.delegation.task"
    _description = "TW Boom Delegation Task"
    _order = "id desc"


    # 7: defaults methods

    # 8: fields
    display_name = fields.Char(default="Delegasi Task")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    
    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch')
    job_id = fields.Many2one('hr.job', 'Job')
    category_id = fields.Many2one('tw.boom.category', 'Category')

    delegation_line_ids = fields.One2many('tw.boom.delegation.task.line', 'delegation_id', 'Delegation Line')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id', 'job_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.company_id.name} - {rec.job_id.name}"
            
    @api.onchange('start_date', 'end_date')
    def _onchange_start_end_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise Warning("Start Date must be less than End Date")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.job_id = False
        self.start_date = False
        self.end_date = False
        self.delegation_line_ids = False
    
    # 12: override methods
    
    # 13: action methods
    def action_search_task(self, is_done=False):
        self.delegation_line_ids = False
        if is_done:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

        data_task = self.env['tw.boom.task'].search([
            ('company_id', '=', self.company_id.id),
            ('job_id', '=', self.job_id.id),
            ('category_id', '=', self.category_id.id),
            ('state', '=', 'open'),
            ('pic_status', '=', 'current_pic'),
            ('transaction_date', '>=', self.start_date),
            ('transaction_date', '<=', self.end_date),
        ])

        if not data_task:
            raise Warning(f'Tidak ada data Boom Task yang dapat didelegasi untuk Branch [{self.company_id.code}] {self.company_id.name} dengan PIC Job {self.job_id.name} !')

        list = []
        for data in data_task:
            list.append((0, 0, {
                'boom_task_id': data.id,
                'category_id': data.category_id.id,
                'no_transaction': data.no_transaction,
                'transaction_value': data.transaction_value,
                'job_delegation_id': data.job_delegation_id.id
            }))
        self.delegation_line_ids = list

    def action_assign_task_to_delegation(self):
        is_exist_checlist_objs = self.delegation_line_ids.filtered(lambda line: line.is_check == True)
        if not is_exist_checlist_objs:
            raise Warning("Pilih Task Yang Akan Didelegasikan")

        for data in is_exist_checlist_objs:
            boom_task_obj = data.boom_task_id
            emp_delegate_obj = self.env['hr.employee'].search([
                ('job_id', '=', boom_task_obj.job_delegation_id.id),
                ('company_id', '=', boom_task_obj.company_id.id),
                ('active', '=', True),
                ('working_end_date', '=', False)], limit=1)
            if not emp_delegate_obj:
                raise Warning(f"PIC Delegasi Tidak Ditemukan untuk task {boom_task_obj.no_transaction}")
            
            prev_employee_obj = boom_task_obj.employee_id
            boom_task_obj.suspend_security().write({
                'previous_employee_id': prev_employee_obj.id,
                'employee_id': emp_delegate_obj.id,
                'job_id': boom_task_obj.job_delegation_id.id,
                'pic_status': 'delegated',
            })

            vals = {
                'employee_id': emp_delegate_obj.id,
                'task_id': boom_task_obj.id,
                'job_id': emp_delegate_obj.job_id.id,
                'company_id': boom_task_obj.company_id.id,
                'assign_date': datetime.now(),
            }
            self.env['tw.boom.task.history.user'].create(vals)
        self.action_search_task(is_done=True)

    def action_check_all_tasks(self):
        if not self.delegation_line_ids:
            raise Warning(f"Tidak ada data yang dapat didelegasikan untuk Branch [{self.company_id.kode_dealer}] {self.company_id.name} dengan PIC Job {self.job_id.name} !")
        for data in self.delegation_line_ids:
            if data.is_check:
                data.is_check = False
            else:
                data.is_check = True

    # 14: private methods
    
    # 15: public methods
    
    # 16: other methods


class TWBoomDelegationTaskLine(models.TransientModel):
    _name = "tw.boom.delegation.task.line"
    _description = "TW Boom Delegation Task Line"
    _order = "id desc"

    # 7: defaults methods

    # 8: fields
    no_transaction = fields.Char('No Transaksi')
    is_check = fields.Boolean(string='Check?', help='', default=False)
    transaction_value = fields.Float('Nilai Transaksi (Rp.)')
    
    # 9: relation fields
    delegation_id = fields.Many2one('tw.boom.delegation.task', 'Delegation')
    boom_task_id = fields.Many2one('tw.boom.task', 'Boom Task')
    category_id = fields.Many2one('tw.boom.category', 'Category')
    job_delegation_id = fields.Many2one('hr.job', 'Job Delegasi')
    