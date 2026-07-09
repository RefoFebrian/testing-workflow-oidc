# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning, ValidationError


class TwApprovalDelegation(models.Model):
    _name = "tw.approval.delegation"
    _inherit = ["mail.thread", "mail.activity.mixin", "tw.approval.mixin"]
    _description = "Approval Delegation"
    _order = "id desc"

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies.filtered(lambda company: company.parent_id)
        if len(company_ids) == 1:
            return company_ids.id
        return False

    # 8: fields
    name = fields.Char(string="Number", required=True, copy=False, readonly=True, default="/", tracking=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today, tracking=True)
    start_date = fields.Date(string="Start Date", required=True, tracking=True)
    end_date = fields.Date(string="End Date", required=True, tracking=True)
    reason = fields.Text(string="Reason", required=True, tracking=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_for_approval', 'Waiting For Approval'),
            ('approved', 'Approved'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        string="State",
        default='draft',
        copy=False,
        tracking=True,
    )
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(),string="Division",default='Umum',required=True,tracking=True,)
    is_added = fields.Boolean(string="Is Added",default=False,copy=False,tracking=True,help="Checked only when this transaction adds the delegated approval group to the delegate user.",)
    is_active = fields.Boolean(string="Is Active",default=False,copy=False,tracking=True,help="Checked while the delegation period is active.",)

    # Audit Trail
    approved_uid = fields.Many2one('res.users', string="Approved By", copy=False, readonly=True)
    approved_date = fields.Datetime(string="Approved On", copy=False, readonly=True)
    confirm_uid = fields.Many2one('res.users', string="Confirmed By", copy=False, readonly=True)
    confirm_date = fields.Datetime(string="Confirmed On", copy=False, readonly=True)
    completed_uid = fields.Many2one('res.users', string="Completed By", copy=False, readonly=True)
    completed_date = fields.Datetime(string="Completed On", copy=False, readonly=True)
    cancel_uid = fields.Many2one('res.users', string="Cancelled By", copy=False, readonly=True)
    cancel_date = fields.Datetime(string="Cancelled On", copy=False, readonly=True)

    # 9: relation fields
    company_id = fields.Many2one('res.company',string="Branch",required=True,default=_get_default_branch,domain="[('parent_id', '!=', False)]",tracking=True,)
    employee_id = fields.Many2one('hr.employee',string="Leave Employee",required=True,tracking=True,)
    delegate_employee_id = fields.Many2one('hr.employee',string="Delegate Employee",required=True,tracking=True,)
    group_id = fields.Many2one('res.groups',string="Group",compute='_compute_group_id',store=True,readonly=True,)
    employee_user_id = fields.Many2one('res.users',string="Leave User",related='employee_id.user_id',store=True,readonly=True,)
    delegate_user_id = fields.Many2one('res.users',string="Delegate User",related='delegate_employee_id.user_id',store=True,readonly=True,)
    
    # 10: constraints & sql constraints
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Delegation number must be unique.'),
    ]

    # 11: compute/depends & on change methods
    @api.depends('employee_id.job_id.group_id')
    def _compute_group_id(self):
        for record in self:
            record.group_id = record.employee_id.job_id.group_id

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date < record.start_date:
                raise ValidationError(_("End date cannot be earlier than start date."))

    @api.constrains('company_id', 'employee_id', 'delegate_employee_id')
    def _check_branch_employee(self):
        for record in self:
            if record.employee_id and record.company_id and record.employee_id.company_id != record.company_id:
                raise ValidationError(_("Leave employee must belong to the selected branch."))

            if record.delegate_employee_id and record.company_id and record.delegate_employee_id.company_id != record.company_id:
                raise ValidationError(_("Delegate employee must belong to the selected branch."))

    @api.constrains('employee_id', 'delegate_employee_id', 'group_id')
    def _check_delegate_requirements(self):
        for record in self:
            if record.employee_id and record.delegate_employee_id and record.employee_id == record.delegate_employee_id:
                raise ValidationError(_("Leave employee and delegate employee must be different."))

            if record.employee_id and not record.group_id:
                raise ValidationError(_("The leave employee's job does not have an approval group yet."))

            if record.delegate_employee_id and not record.delegate_employee_id.user_id:
                raise ValidationError(_("The delegate employee must have a related user."))

    @api.constrains('employee_id', 'delegate_employee_id', 'group_id', 'start_date', 'end_date', 'state')
    def _check_overlap_delegation(self):
        final_states = ('done', 'cancel')
        for record in self.filtered(
            lambda rec: rec.employee_id and rec.start_date and rec.end_date and rec.state not in final_states
        ):
            base_domain = [
                ('id', '!=', record.id),
                ('state', 'not in', final_states),
                ('start_date', '<=', record.end_date),
                ('end_date', '>=', record.start_date),
            ]

            overlapping_employee = self.search_count(base_domain + [('employee_id', '=', record.employee_id.id)])
            if overlapping_employee:
                raise ValidationError(
                    _("There is already another delegation for this leave employee in the selected period.")
                )

            if record.delegate_employee_id and record.group_id:
                overlapping_delegate = self.search_count(
                    base_domain
                    + [
                        ('delegate_employee_id', '=', record.delegate_employee_id.id),
                        ('group_id', '=', record.group_id.id),
                    ]
                )
                if overlapping_delegate:
                    raise ValidationError(
                        _("The delegate employee already has another delegation for the same approval group in the selected period.")
                    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.employee_id and self.employee_id.company_id != self.company_id:
            self.employee_id = False
        if self.delegate_employee_id and self.delegate_employee_id.company_id != self.company_id:
            self.delegate_employee_id = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and not self.company_id:
            self.company_id = self.employee_id.company_id.id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = sequence.next_by_code('tw.approval.delegation') or '/'
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'cancel', 'done'):
                raise Warning(_('Only draft, cancelled, or done delegations can be deleted.'))
        return super().unlink()

    def get_approve_additional_vals(self):
        self.ensure_one()
        vals = super().get_approve_additional_vals()
        vals.update({
            'approved_uid': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })
        return vals

    # 13: action methods
    def action_request_approval(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_('Only draft delegations can request approval.'))
            record._validate_delegation()
            super(TwApprovalDelegation, record).action_request_approval(value=1, code='other')
        return True

    def action_reject(self):
        return super().action_reject_or_cancel(update_values={'state': 'draft'})

    def action_confirm(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != 'approved':
                raise Warning(_('Only approved delegations can be confirmed.'))
            if record.end_date < today:
                raise Warning(_('This delegation has already passed its end date.'))

            record.write({
                'state': 'confirmed',
                'confirm_uid': self.env.user.id,
                'confirm_date': fields.Datetime.now(),
            })

            if record.start_date <= today <= record.end_date:
                record._activate_delegation()
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ('draft', 'waiting_for_approval', 'approved', 'confirmed'):
                raise Warning(_('Only draft, waiting for approval, approved, or confirmed delegations can be cancelled.'))

            if record.state == 'confirmed':
                record._deactivate_delegation(final_state='cancel')
            else:
                record._cancel_approval_lines(_('Delegation cancelled'))
                record.write({
                    'state': 'cancel',
                    'cancel_uid': self.env.user.id,
                    'cancel_date': fields.Datetime.now(),
                    'is_active': False,
                    'is_added': False,
                })
        return True

    # 14: private methods
    def _validate_delegation(self):
        self.ensure_one()
        if not self.company_id:
            raise Warning(_('Branch is required.'))
        if not self.employee_id:
            raise Warning(_('Leave employee is required.'))
        if not self.delegate_employee_id:
            raise Warning(_('Delegate employee is required.'))
        if not self.group_id:
            raise Warning(_("The leave employee's job does not have an approval group yet."))
        if not self.delegate_user_id:
            raise Warning(_('The delegate employee must have a related user.'))

    def _cancel_approval_lines(self, reason):
        self.ensure_one()
        self.approval_ids.filtered(lambda line: line.state in ('open', 'approve')).suspend_security().write({
            'state': 'cancel',
            'reason': reason,
            'approver_id': self.env.user.id,
            'tanggal': fields.Datetime.now(),
        })

    def _activate_delegation(self):
        self.ensure_one()
        if self.state != 'confirmed' or self.is_active:
            return

        delegate_user = self.delegate_user_id.suspend_security()
        if not delegate_user:
            raise Warning(_('The delegate employee must have a related user.'))

        vals = {'is_active': True}
        if self.group_id not in delegate_user.groups_id:
            delegate_user.write({
                'groups_id': [fields.Command.link(self.group_id.id)],
            })
            vals['is_added'] = True
        else:
            vals['is_added'] = False
        self.write(vals)

    def _has_other_active_delegation(self):
        self.ensure_one()
        if not self.delegate_user_id or not self.group_id:
            return False
        return bool(self.search_count([
            ('id', '!=', self.id),
            ('state', '=', 'confirmed'),
            ('is_active', '=', True),
            ('delegate_user_id', '=', self.delegate_user_id.id),
            ('group_id', '=', self.group_id.id),
        ]))

    def _deactivate_delegation(self, final_state='done'):
        self.ensure_one()
        delegate_user = self.delegate_user_id.suspend_security()

        if self.is_added and delegate_user and not self._has_other_active_delegation():
            delegate_user.write({
                'groups_id': [fields.Command.unlink(self.group_id.id)],
            })

        vals = {
            'state': final_state,
            'is_active': False,
        }
        timestamp = fields.Datetime.now()
        if final_state == 'cancel':
            vals.update({
                'cancel_uid': self.env.user.id,
                'cancel_date': timestamp,
            })
        else:
            vals.update({
                'completed_uid': self.env.user.id,
                'completed_date': timestamp,
            })
        self.write(vals)

    @api.model
    def _cron_sync_delegation_group(self, limit=100):
        today = fields.Date.context_today(self)

        to_activate = self.search([
            ('state', '=', 'confirmed'),
            ('is_active', '=', False),
            ('start_date', '<=', today),
            ('end_date', '>=', today),
        ], order='start_date,id', limit=limit)
        for record in to_activate:
            record._activate_delegation()

        to_finish = self.search([
            ('state', '=', 'confirmed'),
            ('end_date', '<', today),
        ], order='end_date,id', limit=limit)
        for record in to_finish:
            record._deactivate_delegation(final_state='done')
