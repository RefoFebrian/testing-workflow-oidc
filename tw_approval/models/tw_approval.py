# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


#? Model ini untuk membuat form reject atau cancel di transaksional, supaya tidak perlu membuat model masing2
class TwApproval(models.Model):
    _name = "tw.approval"
    _description = "Approval : Default model for doing approvals in transaction"
    _inherit = ['mail.thread','mail.activity.mixin']

    # 7: defaults methods

    # 8: fields
    reason = fields.Text(string="Reason",required=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_approval_reject(self):
        trx_obj = self._search_trx(context=self._context)
        if self.env['tw.approval.matrix'].reject(trx_obj, self.reason):
            self.update_record_with_value_from_context(trx_obj, self._context)

            created = self.sudo()._create_reject_activity(trx_obj)
            if not created:
                return{
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Informasi',
                        'message': 'Notifikasi tidak dibuat karena model ini tidak inherit mail.activity.',
                        'type': 'warning',
                        'sticky': False,
                        'next':{'type':'ir.actions.act_window_close'}
                    },
                }

        else:
            raise Warning("Perhatian ! Anda 'Tidak Dapat' atau 'Sudah' melakukan Approval. \nPeriksa Tab Approval.")
        return True

    def action_approval_cancel(self):
        trx_obj = self._search_trx(context=self._context)
        if self.env['tw.approval.matrix'].cancel_approval(trx_obj, self.reason):
            self.update_record_with_value_from_context(trx_obj, self._context)

        else:
            raise Warning("Perhatian ! Anda 'Tidak Dapat' atau 'Sudah' melakukan Approval. \nPeriksa Tab Approval.")
        return True

    def action_approval_cancel_approved(self):
        trx_obj = self._search_trx(context=self._context)
        reject_reason = "batal approve: "+self.reason
        for approval_line in trx_obj.approval_ids:
            approval_line.write({'state':'cancel'})
        form_id = trx_obj.__class__.__name__
        # Create History
        self.env['tw.approval.line'].create({
            'form_id': form_id.id,
            'state':'cancel',
            'transaction_id': trx_obj.id,
            'approver_id': self._uid,
            'reason': reject_reason,
            'tanggal':datetime.now(),
            'division':trx_obj.division,
        })
        self.update_record_with_value_from_context(trx_obj,self._context)
        return True

    # 14: private methods
    def _search_trx(self,context):
        trx_id = context.get('active_id',False)
        model_name = context.get('model_name',False)

        if not trx_id and not model_name:
            raise Warning('Perhatian ! Context di button belum lengkap.')

        trx_obj = self.env[model_name].browse(trx_id)
        if not trx_obj:
            return Warning(f'Perhatian ! Model {model_name} dengan ID transaksi {trx_id} tidak ditemukan.')

        return trx_obj

    def _create_reject_activity(self, trx_obj):
        # untuk mengirim notifikasi model harus inherit ke mail.activity
        # message_subcriber digunakan untuk mengecek model ini inherit ke mail.activity atau tidak
        # jika tidak langsung return
        if not hasattr(trx_obj,'message_subscribe'):
            return False
        
        requester = trx_obj.create_uid
        if not requester:
            return

        rejection_line = trx_obj.approval_ids.filtered(lambda l: l.state == 'reject')
        approver_name = rejection_line[-1].approver_id.name if rejection_line else 'Approver'

        message = (
            f"Transaksi telah ditolak oleh {approver_name}.\n"
            f"Alasan penolakan:\n\n{self.reason}.\n\n"
            f"Silahkan masukkan perbaikan atau klarifikasi sesuai catatan yang diberikan"
        )

        activity_type = self.env.ref('mail.mail_activity_data_todo')

        source_model = trx_obj._name
        source_model_id = self.env['ir.model']._get(source_model).id
        source_record_id = trx_obj.id

        activities= self.env['mail.activity'].search([('res_id', '=', source_record_id), ('res_model_id', '=', source_model_id),('activity_type_id', '=', activity_type.id),])
        if activities:
            activities.unlink()

        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'res_id': source_record_id,
            'res_model_id': source_model_id,
            'user_id': requester.id,
            'summary': message,
            'note': 'Transaksi ditolak',
            'date_deadline': fields.Date.today(),
        })
        return True

    def update_record_with_value_from_context(self, trx, context):
        update_value = context.get('update_value',False)
        if update_value :
            trx.write(update_value)