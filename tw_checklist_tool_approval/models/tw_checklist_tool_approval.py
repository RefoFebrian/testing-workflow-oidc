# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwChecklistTools(models.Model):
    _name = "tw.checklist.tools"
    _inherit = ["tw.checklist.tools", "tw.approval.mixin", "mail.thread", "mail.activity.mixin"]

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(tracking=True)
    approval_state = fields.Selection(selection_add=[
        ('b', 'Belum Request'),
        ('rf', 'Request for Approval'),
        ('a', 'Approved'),
        ('r', 'Rejected'),
        ('c', 'Closed')
    ], string='Status Approval', default='b', readonly=False, tracking=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_rfa(self, confirmed=False):
        if not confirmed:
            tool_not_checked = False
            today = datetime.today().date()
            for line in self.line_ids:
                if line.date:
                    line_date = line.date
                    if today < line_date:
                        raise UserError(_("Perhatian!\nBelum bisa melakukan RFA karena periode belum mencapai akhir periode."))

                if line.week and line.week != '4':
                    raise UserError(_(
                        "Perhatian!\nBelum bisa melakukan RFA karena periode belum mencapai akhir periode. (minggu ke-4)."))

                for detail_line in line.checklist_detail_ids:
                    if not detail_line.tools_state:
                        tool_not_checked = True
                        break

            if tool_not_checked:
                return {
                    'name': 'Konfirmasi RFA',
                    'type': 'ir.actions.act_window',
                    'res_model': 'tw.upload.message.wizard',
                    'view_mode': 'form',
                    'view_id': self.env.ref('tw_checklist_tool.view_tw_import_result_message_wizard').id,
                    'target': 'new',
                    'context': {
                        'message': "Perhatian!\nTerdapat tools yang belum di cek kondisinya pada salah satu periode. Apakah Anda yakin ingin melakukan RFA?",
                        'default_parent_id': self.id,
                        'method_to_call': 'action_rfa',
                    }
                }

        obj_matrix = self.env['tw.approval.matrix'].request_by_value(self, 5)
        if obj_matrix:
            self.suspend_security().write({
                'state': 'RFA',
                'approval_state': 'rf'
            })

    def action_approved(self):
        approval_sts = self.env["tw.approval.matrix"].approve(self)
        if approval_sts == 1:
            self.suspend_security().write({
                'approval_state': "a",
                'state': "approve",
            })
        elif approval_sts == 0:
            raise UserError(_('Perhatian !\n User tidak termasuk group approval atau sudah melakukan approval sebelumnya.'))
        elif approval_sts == 2:
            raise UserError(_('Perhatian !\n Masih ada data Approval yang belum diproses untuk limit group di bawah Anda.'))
        return True

    def action_reject_or_cancel(self, update_values=None):
        window_title = self._context.get('window_title', 'Reject')
        validate_state = ['RFA', 'done']
        
        if self.state not in validate_state:
             raise UserError(_('Silakan refresh halaman ini, state tidak sesuai.'))

        if hasattr(self, '_check_groups'):
            self._check_groups()

        wizard_form_ref = 'tw_approval.tw_approval_reject_wizard_form_view'
        if window_title == 'Cancel':
            wizard_form_ref = 'tw_approval.tw_cancel_approval_wizard_form_view'
        
        self.ensure_one()
        form_id = self.env.ref(wizard_form_ref).id
            
        if update_values is None:
            update_values = {'state': 'open', 'approval_state': 'r'}
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.approval',
            'name': f'{window_title} Approval {self._description}',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,
            'target': 'new',
            'context': {
                'model_name': self._name,
                'update_value': update_values,
                'active_id': self.id,
                'active_model': self._name,
            },
        }


    # 14: private methods
