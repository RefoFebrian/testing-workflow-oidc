# 1: imports of python lib
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from math import radians, sin, cos, acos
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class AttendanceRequest(models.Model):
    _name = "tw.attendance.request"
    _description = "Attendance Request"

    # 7: defaults methods
    def _get_default_employee(self):
        return self.env.user.employee_id.id

    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    # 8: fields
    name = fields.Char('Name', default='New')
    date = fields.Date('Date', default=_get_default_date)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wfa', 'Waiting for Approval'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed'),
    ], string='State', default='draft')
    reject_reason = fields.Text('Reject Reason')

    # Audit Trail Fields
    approve_uid = fields.Many2one('res.users', string='Approved By')
    approve_date = fields.Datetime('Approved Date')
    confirm_uid = fields.Many2one('res.users', 'Confirmed By')
    confirm_date = fields.Datetime('Confirmed On')
    reject_uid = fields.Many2one('res.users', string='Rejected By')
    reject_date = fields.Datetime('Rejected Date')

    # 9: relation fields
    employee_id = fields.Many2one('hr.employee', 'Name', default=_get_default_employee)
    request_line_ids = fields.One2many('tw.attendance.request.line', 'request_id', string='Request Lines')

    # 10: constraints & sql constraints
    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model
    def create(self,vals):
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].sudo().browse(vals['employee_id'])
        else:
            employee = self.employee_id.sudo().search([('user_id','=',self._context.get('uid'))])
        vals['name'] = str(employee.name) + " (" + str(self._get_default_date()) + ")"
        return super(AttendanceRequest, self).create(vals)

    # 13: action methods
    def action_rfa(self):
        self.write({'state': 'wfa'})

    def action_reject(self):
        form_id = self.env.ref('tw_hr_attendance.tw_attendance_request_reject_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Attendance Request',
            'res_model': 'tw.attendance.request',
            'res_id': self.id,
            'view_id': form_id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_reject_confirm(self):
        self.write({
            'state': 'rejected',
            'reject_uid': self._uid,
            'reject_date': self._get_default_datetime()
        })

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approve_uid': self._uid,
            'approve_date': self._get_default_datetime()
        })

    def action_confirm(self):
        self.write({
            'state': 'confirmed',
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_datetime()
        })


class AttendanceRequestLine(models.Model):
    _name = "tw.attendance.request.line"
    _description = "Attendance Request Line"

    request_id = fields.Many2one('tw.attendance.request', string='Attendance Request', ondelete='cascade')
    date = fields.Date('Date')
    start_date = fields.Datetime('Start Time', required=True)
    end_date = fields.Datetime('End Time', required=True)
    reason = fields.Text('Reason')
    work_place_id = fields.Many2one('res.company', string="Workplace")

    @api.constrains('start_date', 'end_date')
    def check_if_date_valid(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise Warning('Waktu tidak valid !\nWaktu Berakhir tidak boleh lebih kecil dari Waktu Mulai !')