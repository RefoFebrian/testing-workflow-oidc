from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderAssetCancel(models.Model):
    _name = "tw.purchase.order.asset.cancel"
    _description = 'Purchase Order Asset Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'

    def _get_default_date(self):
        return fields.Date.context_today(self)

    def _get_default_datetime(self):
        return fields.Datetime.now()

    division = fields.Selection(
        selection=lambda self: self.env['tw.selection'].get_division_options(),
        default='Umum'
    )

    purchase_order_asset_id = fields.Many2one('purchase.order.asset', 'Purchase Order Asset')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('purchase_order_asset_id'):
                po_asset = self.env['purchase.order.asset'].browse(vals['purchase_order_asset_id'])
                vals['transaction_name'] = po_asset.name
                name = "X" + po_asset.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + po_asset.name
                vals['date'] = self._get_default_date()
        return super(PurchaseOrderAssetCancel, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError('Transaksi yang berstatus selain Draft tidak bisa dihapus.')
        return super(PurchaseOrderAssetCancel, self).unlink()

    def action_request_approval(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        
        self._cek_purchase_order_asset()
        total_value = self.purchase_order_asset_id.amount_total
        return super().action_request_approval(value=total_value)

    def action_approved(self):
        self.ensure_one()
        self._cek_purchase_order_asset()
        approval_sts = self.env['tw.approval.matrix'].approve(self)
        if approval_sts == 1:
            self.write({
                'approval_state': 'a',
                'state': 'approved'
            })
        elif approval_sts == 0:
            raise UserError('Perhatian!\n User tidak termasuk group approval')
        return True

    def action_confirm(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        
        self._cek_purchase_order_asset()
        self.purchase_order_asset_id.write({
            'state': 'cancel',
        })
        self.write({
            'state': 'confirmed',
            'confirm_date': self._get_default_datetime(),
            'confirm_uid': self.env.user.id,
        })

    def action_print_document_po_asset_cancel(self):
        return self.env.ref('purchase_order_asset_cancel.action_print_document_po_asset_cancel').report_action(self)

    def _cek_purchase_order_asset(self):
        gr_lines = self.env['tw.good.receive.asset.line'].search([
            ('purchase_order_id.id','=',self.purchase_order_asset_id.id),
            ('state','in',['open','done'])
        ])
        if gr_lines:
            gr_name = ', '.join([name for name in gr_lines.mapped('name') if name])
            raise UserError(
                f'PO Asset {self.purchase_order_asset_id.name} masih memiliki GR {gr_name}'
                f'Silakan lakukan pembatalan GR terlebih dahulu!'
            )

    def _check_duplicate_transaction(self, name) :
        return self.cancellation_id._check_duplicate_transaction(name)