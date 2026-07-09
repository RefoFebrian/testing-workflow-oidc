# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class JournalMemorialApproval(models.Model):
    """Extension of Journal Memorial with approval workflow.
    
    Handles two approval flows distinguished by `is_cancel_request`:
    - RFA (Request for Approval): standard approval before confirmation.
    - Cancel Approval: approval before cancellation of a confirmed record.
    Both flows use the same `waiting_for_approval` state.
    """
    _name = "tw.journal.memorial"
    _inherit = ["tw.journal.memorial","tw.approval.mixin"]

    # 8: fields
    state = fields.Selection(
        selection_add=[
            ('draft',),
            ('waiting_for_approval','Waiting For Approval'),
            ('approved','Approved'),
            ('confirm',),
        ], 
        ondelete={
            'waiting_for_approval': 'set default',
            'approved': 'set default',
        }
    )

    is_cancel_request = fields.Boolean(
        string="Is Cancel Request", default=False, copy=False,
        help="Flag to distinguish cancel approval from RFA approval when state is waiting_for_approval."
    )

    is_need_approval_cancel = fields.Boolean(
        compute="_compute_is_need_approval_cancel", store=False
    )

    cancel_source_id = fields.Many2one('tw.journal.memorial', string='Cancel Source', copy=False)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_is_need_approval_cancel(self):
        """Check branch setting to determine if cancellation needs approval."""
        for rec in self:
            rec.is_need_approval_cancel = False
            if rec.company_id:
                branch_setting = self.env['tw.branch.setting'].suspend_security().search(
                    [('company_id', '=', rec.company_id.id)], limit=1
                )
                if branch_setting and branch_setting.is_need_approval_jm_cancel:
                    rec.is_need_approval_cancel = True

    # 12: override methods
    def get_approve_additional_vals(self):
        """Override: return correct target state based on approval context."""
        self.ensure_one()
        if self.is_cancel_request:
            return {'state': 'cancel'}
        return super().get_approve_additional_vals()

    # 13: action methods
    def action_request_approval(self, value=None, code='other', **kwargs):
        self._validate_journal_memorial()
        # Mengajukan permintaan approval
        return super().action_request_approval(value or self.total_debit, code, **kwargs)

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            if rec.cancel_source_id and rec.cancel_source_id.state == 'confirm':
                rec.cancel_source_id.write({
                    'state': 'cancel',
                    'cancel_refered_id': rec.id,
                })
        return res

    def action_cancel(self):
        """Override: route cancellation through approval if branch setting requires it."""
        self.ensure_one()
        if self.state != 'confirm':
            raise Warning(_('Only confirmed Journal Memorials can be cancelled!'))

        branch_setting = self.env['tw.branch.setting'].suspend_security().search(
            [('company_id', '=', self.company_id.id)], limit=1
        )

        if branch_setting and branch_setting.is_need_approval_jm_cancel:
            existing_cancel = self.env['tw.journal.memorial'].search([
                ('cancel_source_id', '=', self.id),
                ('state', 'not in', ('cancel',))
            ], limit=1)
            
            if existing_cancel:
                message = _('A cancellation request is already in progress: %s') % existing_cancel.name
                if existing_cancel.state == 'confirm':
                    message = _('This Journal Memorial has already been cancelled by %s') % existing_cancel.name
                raise Warning(message)

            line_vals = []
            for line in self.line_ids:
                line_vals.append(Command.create({
                    'account_id': line.account_id.id,
                    'amount': line.amount,
                    'type': 'debit' if line.type == 'credit' else 'credit',
                    'name': line.name,
                    'company_id': line.company_id.id,
                    'partner_id': line.partner_id.id if line.partner_id else False,
                    'asset_id': line.asset_id.id if line.asset_id else False,
                }))

            reciprocal_vals = {
                'company_id': self.company_id.id,
                'period_id': self.period_id.id,
                'current_period_id': self.current_period_id.id,
                'description': 'Cancel Journal Memorial No %s' % self.name,
                'division': self.division,
                'date': date.today(),
                'is_auto_reverse': self.is_auto_reverse,
                'code': 'cancel',
                'journal_id': self.journal_id.id,
                'line_ids': line_vals,
                'cancel_source_id': self.id,
            }
            reciprocal = self.sudo().create(reciprocal_vals)

            reciprocal.action_request_approval(value=reciprocal.total_debit, code='cancel')

            return {
                'name': _('Cancellation Journal Memorial'),
                'type': 'ir.actions.act_window',
                'res_model': 'tw.journal.memorial',
                'view_mode': 'form',
                'res_id': reciprocal.id,
                'target': 'current',
            }
        else:
            # Direct cancel without approval
            super().action_cancel()

    def action_view_cancel_jm(self):
        """Navigate to the cancellation JM record."""
        self.ensure_one()
        if not self.cancel_refered_id:
            return
        return {
            'name': _('Cancel Journal Memorial'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.journal.memorial',
            'view_mode': 'form',
            'res_id': self.cancel_refered_id.id,
            'target': 'current',
        }

    def action_approval(self):
        """Override: trigger reciprocal record creation after cancel approval is fully approved."""
        is_cancel = self.is_cancel_request
        result = super().action_approval()
        
        # If all approvals passed (result == 1) and this was a cancel approval,
        # create the reciprocal record
        if result == 1 and is_cancel:
            self._create_reciprocal_record()
        return result