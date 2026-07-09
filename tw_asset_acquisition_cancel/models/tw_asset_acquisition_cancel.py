# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TwAssetAcquisitionCancel(models.Model):
    _name = "tw.asset.acquisition.cancel"
    _description = 'Asset Acquisition Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'

    # 7: defaults methods
    def _get_default_date(self):
        return fields.Date.context_today(self)

    def _get_default_datetime(self):
        return fields.Datetime.now()

    # 8: fields
    division = fields.Selection(
        selection=lambda self: self.env['tw.selection'].get_division_options(),
        default='Umum'
    )

    # 9: relation fields
    asset_acquisition_id = fields.Many2one(comodel_name='tw.asset.acquisition', string='Asset Acquisition')
    amount_total = fields.Float(string='Total', related='asset_acquisition_id.amount_total', store=False)
    cancellation_id = fields.Many2one(comodel_name='tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('asset_acquisition_id'):
                ac_obj = self.env['tw.asset.acquisition'].browse(vals['asset_acquisition_id'])
                vals['transaction_name'] = ac_obj.name
                name = 'X' + ac_obj.name
                self._check_duplicate_transaction(name)
                vals['name'] = 'X' + ac_obj.name
                vals['date'] = self._get_default_date()
        
        return super(TwAssetAcquisitionCancel, self).create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning('Transaksi yang berstatus selain Draft tidak bisa dihapus.')
        
        return super(TwAssetAcquisitionCancel, self).unlink()

    # 13: action methods
    def action_asset_acquisition_cancel_tree(self):
        domain = [('asset_acquisition_id','!=',False)]
        name = 'Asset Acquisition Cancel'
        list_view_id = self.env.ref('tw_asset_acquisition_cancel.tw_asset_acquisition_cancel_list_view').id
        form_view_id = self.env.ref('tw_asset_acquisition_cancel.tw_asset_acquisition_cancel_form_view').id
        search_view_id = self.env.ref('tw_asset_acquisition_cancel.tw_asset_acquisition_cancel_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.asset.acquisition.cancel',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'search_default_state_draft': 1,
                'search_default_state_waiting_for_approval': 1,
                'search_default_state_approved': 1,
                'default_model_id': self.env.ref('tw_asset_management.model_tw_asset_acquisition'),
                'default_model_type': 'tw.asset.acquisition',
                'readonly_by_pass': 1
            },
        }
    
    def action_request_approval(self):
        self.ensure_one()
        if self.state != 'draft':
            raise Warning(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        
        total_value = self.asset_acquisition_id.amount_total
        if not total_value:
            raise Warning(f'Asset Acquisition {self.asset_acquisition_id.name} tidak memiliki nilai total.'
                            f'Pastikan amount telah terisi di Asset Acquisition')
        return super().action_request_approval(value=total_value)

    def action_approved(self):
        self.ensure_one()
        approval_sts = self.env['tw.approval.matrix'].approve(self)
        if approval_sts == 1:
            self.write({
                'approval_state': 'a',
                'state': 'approved'
            })
        elif approval_sts == 0:
            raise Warning('Perhatian!\n User tidak termasuk group approval')
        
        return True

    def action_confirm(self):
        self.ensure_one()
        if self.state != 'approved':
            raise Warning(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        
        self.asset_acquisition_id.with_context(tracking_disable=True).action_cancel()

        self.write({
            'state': 'confirmed',
            'confirm_date': self._get_default_datetime(),
            'confirm_uid': self.env.user.id,
        })

    # 14: private methods
    def _check_duplicate_transaction(self, name):
        return self.cancellation_id._check_duplicate_transaction(name)