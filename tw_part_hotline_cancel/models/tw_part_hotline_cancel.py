from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class PartHotlineCancel(models.Model):
    _name = "tw.part.hotline.cancel"
    _description = 'Part Hotline Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread','tw.approval.mixin']
    _order = 'id desc'
   
    def _get_default_date(self):
        return fields.Date.context_today(self)
    
    def _get_default_datetime(self):
        return fields.Datetime.now()

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Sparepart')

    part_hotline_id = fields.Many2one('tw.part.hotline', 'Part Hotline')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('part_hotline_id'):
                hotline_id = self.env['tw.part.hotline'].browse(vals['part_hotline_id'])
                vals['transaction_name'] = hotline_id.name
                name = "X" + hotline_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + hotline_id.name
                vals['date'] = self._get_default_date()
        return super(PartHotlineCancel,self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError('Transaksi yang berstatus selain Draft tidak bisa dihapus.')
        return super(PartHotlineCancel, self).unlink()
        
    
    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        self.ensure_one()
        self._cek_hotline()
        total_value = 20000000
        return super().action_request_approval(value=total_value)

    def action_approved(self):
        self.ensure_one()
        self._cek_hotline()
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
        self._check_po_cancel()
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        self.ensure_one()
        self._cek_hotline()
        self.part_hotline_id.write({
            'state': 'cancel',
            'cancel_uid': self.env.user.id,
            'cancel_date': self._get_default_datetime(),
        })
        self.write({
            'state': 'confirmed',
            'confirm_date': self._get_default_datetime(),
            'confirm_uid': self.env.user.id,
        })

    def action_print_document_hotline_cancel(self):
        return self.env.ref('tw_part_hotline_cancel.action_print_document_hotline_cancel').report_action(self)

    def _cek_hotline(self):
        po_obj = self.env['purchase.order'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('part_hotline_id', '=', self.part_hotline_id.id)
        ])
        for po in po_obj:
            if po.state != 'cancel':
                raise UserError(
                    f'Part Hotline {self.part_hotline_id.name} sudah melakukan Purchase Order {po.name}, silahkan di batalkan terlebih dahulu!'
                )
        wo_obj = self.env['tw.work.order'].sudo().search([
            ('order_line.part_hotline_id', '=', self.part_hotline_id.id)
        ])
        for wo in wo_obj:
            if wo.state != 'cancel':
                raise UserError(
                    f'Part Hotline {self.part_hotline_id.name} sudah melakukan Work Order {wo.name}, silahkan di batalkan terlebih dahulu!'
                )

        ps_obj = self.env['tw.part.sales'].sudo().search([
            ('order_line.part_hotline_id', '=', self.part_hotline_id.id)
        ])
        for ps in ps_obj:
            if ps.state != 'cancel':
                raise UserError(
                    f'Part Hotline {self.part_hotline_id.name} sudah melakukan Part Sales {ps.name}, silahkan di batalkan terlebih dahulu!'
                )

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

    def _check_po_cancel(self):
        # Cancel PO Draft, PO draft is filtered by domain view, thus no need to map draft state
        if self.part_hotline_id.purchase_order_id:
            if self.part_hotline_id.purchase_order_id.state not in ['draft','cancel']:
                raise UserError(
                    f'Purchase order {self.part_hotline_id.purchase_order_id.name} sudah bukan Draft atau Cancel, silahkan di batalkan terlebih dahulu!'
                )
            self.part_hotline_id.purchase_order_id.sudo().button_cancel()
