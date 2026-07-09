# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import traceback
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class TWBoomLeaveRequest(models.Model):
    _name = "tw.boom.leave.request"
    _description = "TW Boom Leave Request"

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string="Name")
    reason = fields.Text(string="Alasan")
    nik_pic = fields.Char(string="NIK PIC", compute='_compute_pic_details', store=True)

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="State", default="draft")


    # Audit Trail
    approved_uid = fields.Many2one('res.users','Approved by')
    approved_date = fields.Datetime('Approved on')
    rejected_uid = fields.Many2one('res.users','Rejected by')
    rejected_date = fields.Datetime('Rejected on')
    
    # 9: relation fields
    pic_id = fields.Many2one('hr.employee', string="PIC")
    job_id = fields.Many2one('hr.job', string="Job Title", compute='_compute_pic_details', store=True)
    company_id = fields.Many2one('res.company', string="Branch", compute='_compute_pic_details', store=True)

    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise Warning('End date tidak boleh kurang dari start date!')

            if record.start_date and record.start_date < date.today():
                raise Warning('Start date tidak boleh kurang dari hari ini!')

    @api.depends('pic_id')
    def _compute_pic_details(self):
        for record in self:
            record.nik_pic = record.pic_id.registry_number
            record.job_id = record.pic_id.job_id
            record.company_id = record.pic_id.company_id

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        # Ensure start_date is checked against end_date only when both are set
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Warning('End date tidak boleh kurang dari start date!')

        if self.start_date and self.start_date < date.today():
            raise Warning('Start date tidak boleh kurang dari hari ini!')

    def _auto_delegate_task_boom(self):
        data = self.sudo().search([
            ('state','=','approved'),
            ('start_date','<=',date.today())
        ])
        if data:
            pic_ids = [pic.pic_id.id for pic in data]
            for pic in data:
                curr_employee_id = pic.pic_id.id
                boom_task_obj = self.env['tw.boom.task'].search([
                    ('employee_id', '=', curr_employee_id),
                    ('state', '!=', 'done'),
                    ('pic_status', '=', 'current_pic')
                ])
                if boom_task_obj:
                    for task in boom_task_obj:
                        note_delegate = False
                        job_id = task.job_delegation_id.id

                        emp_delegate_obj = self.env['hr.employee'].search([
                            ('job_id', '=', job_id),
                            ('company_id', '=', task.company_id.id),
                            ('active', '=', True),
                            ('working_end_date', '=', False)], limit=1)

                        if emp_delegate_obj.id not in pic_ids:
                            employee_id = emp_delegate_obj.id
                            job_id = emp_delegate_obj.job_id.id
                            pic_status = 'delegated'
                        else:
                            job_obj = self.env['hr.job'].search([('name', '=', 'ADMINISTRATION SPV')], limit=1)
                            query = f"""
                                SELECT emp.id
                                FROM res_area area
                                LEFT JOIN res_area_company_rel racr ON racr.area_id = area.id
                                LEFT JOIN hr_employee emp ON emp.area_id = area.id
                                WHERE racr.company_id = {pic.employee_id.branch_id.id}
                                AND emp.job_id = {job_obj.id}
                                AND emp.active = TRUE
                                AND emp.working_end_date isnull
                            """
                            self._cr.execute(query)
                            aas_delegate_obj = self._cr.fetchone()
                            if aas_delegate_obj:
                                employee_id = aas_delegate_obj[0]
                                job_id = job_obj.id
                                pic_status = 'delegated'
                            else:
                                job_obj = self.env['hr.job'].search([('name', '=', 'ADMINISTRATION HEAD')], limit=1)
                                company_obj = self.env['res.company'].search([
                                    ('id', '!=', pic.employee_id.company_id.id),
                                    ('district_id', '=', pic.employee_id.company_id.district_id.id)
                                ], limit=1)

                                near_delegate_obj = self.env['hr.employee'].search([
                                    ('company_id', '=', company_obj.id),
                                    ('job_id', '=', job_obj.id),
                                    ('active', '=', True),
                                    ('working_end_date', '=', False)], limit=1)

                                if near_delegate_obj.id not in pic_ids:
                                    employee_id = near_delegate_obj.id
                                    job_id = near_delegate_obj.job_id.id
                                    pic_status = 'delegated'
                                else:
                                    note_delegate = "Gagal Delagate Task Karena tidak ada PIC yang ready untuk didelegasikan."
                                
                        if not note_delegate:
                            task.suspend_security().write({
                                'employee_id': employee_id,
                                'previous_employee_id': curr_employee_id,
                                'job_id': job_id,
                                'pic_status': pic_status
                            })

                            vals = {
                                'task_id': task.id,
                                'employee_id': employee_id,
                                'job_id': job_id,
                                'company_id': task.company_id.id,
                                'assign_date': datetime.now(),
                            }
                            self.env['tw.boom.task.history.user'].suspend_security().create(vals)
                        else:
                            task.suspend_security().write({
                                'note_delegate': note_delegate
                            })