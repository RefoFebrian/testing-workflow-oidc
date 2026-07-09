from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class GoodReceiveAssetCancel(models.Model):
    _name = "tw.good.receive.asset.cancel"
    _description = 'Good Receive Asset Cancel'
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

    good_receive_id = fields.Many2one('tw.good.receive', 'Good Receive Asset')
    amount_total = fields.Float(string='Total', related='good_receive_id.amount_total', store=False)
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('good_receive_id'):
                gr = self.env['tw.good.receive'].browse(vals['good_receive_id'])
                vals['transaction_name'] = gr.name
                name = "X" + gr.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + gr.name
                vals['date'] = self._get_default_date()
        return super(GoodReceiveAssetCancel, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError('Transaksi yang berstatus selain Draft tidak bisa dihapus.')
        return super(GoodReceiveAssetCancel, self).unlink()

    def action_request_approval(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')

        self._cek_good_receive_asset()
        total_value = self.good_receive_id.amount_total
        if not total_value:
            raise UserError(f'Good Receive {self.good_receive_id.name} tidak memiliki nilai total.'
                            f'Pastikan harga telah terisi di GR')
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
            raise UserError('Perhatian!\n User tidak termasuk group approval')
        return True

    def action_confirm(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        
        self._cek_good_receive_asset()
        self.good_receive_id.with_context(tracking_disable=True).action_cancel()
        
        # self.reverse_move()
        self.write({
            'state': 'confirmed',
            'confirm_date': self._get_default_datetime(),
            'confirm_uid': self.env.user.id,
        })

    def action_print_document_gr_asset_cancel(self):
        return self.env.ref('tw_gr_asset_cancel.action_print_document_gr_asset_cancel').report_action(self)

    # def _cek_good_receive_asset(self):
    #     gr = self.good_receive_id

    #     # Pengecekkan invoice
    #     if gr.account_move_id and gr.account_move_id.payment_state == 'paid':
    #         raise UserError(
    #             f'Good Receive {gr.name} tidak bisa dibatalkan karena invoice sudah dibayar!'
    #         )

    #     # Pengecekkan akuisisi
    #     acquired_lines = gr.move_asset_ids.filtered(lambda l: l.is_acquired)
    #     if acquired_lines:
    #         acquired_products = ', '.join(acquired_lines.mapped('product_id.name'))
    #         raise UserError(
    #             f'Good Receive {gr.name} tidak bisa dibatalkan karena sudah ada Akuisisi '
    #             f'untuk produk: {acquired_products}. '
    #             f'Silakan batalkan Akuisisi terlebih dahulu!'
    #         )

    # def _check_duplicate_transaction(self, name):
    #     return self.cancellation_id._check_duplicate_transaction(name)

    # def reverse_move(self):
    #     move = self.good_receive_id.account_move_id
    #     if not move:
    #         raise UserError("No accounting entry found for this payment.")
        
    #     # Unreconcile Collecting Entries
    #     move_line_collecting = move.line_ids
    #     move_line_collecting.action_unreconcile_match_entries()

    #     account_setting = self.company_id.branch_setting_id.account_setting_id
    #     journal_collecting_id = account_setting.journal_collecting_id
    #     if not journal_collecting_id:
    #         raise UserError("Please set Journal Collecting Cancel in Account Setting branch %s." % self.company_id.name)
        
    #     default_values_list = [{
    #         'name': self.name,
    #         'ref': f'Reversal of: {move.name}',
    #         'date': fields.Date.context_today(self),
    #         'invoice_date': fields.Date.context_today(self),
    #         'journal_id': journal_collecting_id.id,
    #     }]
        
    #     reversed_move = move._reverse_moves(
    #         default_values_list=default_values_list,
    #         cancel=True
    #     )
    #     return reversed_move