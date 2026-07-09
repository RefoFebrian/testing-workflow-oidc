# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class TwOwnershipDocumentHandoverCancel(models.Model):
    _name = "tw.ownership.document.handover.cancel"
    _description = 'Penyerahan BPKB Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'

    def _get_default_date(self):
        return fields.Date.today()

    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    document_ownership_handover_id = fields.Many2one(
        'tw.vehicle.ownership.handover',
        string='Penyerahan BPKB',
        required=True,
    )
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.document_ownership_handover_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('document_ownership_handover_id'):
                handover = self.env['tw.vehicle.ownership.handover'].browse(vals['document_ownership_handover_id'])
                vals['transaction_name'] = handover.name
                name = "X" + handover.name
                self._check_duplicate_transaction(name)
                vals['name'] = name
                vals['date'] = self._get_default_date()
        return super().create(vals_list)

    def _validity_check(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            if not rec.document_ownership_handover_id:
                raise ValidationError(_('Please select an ownership document handover to cancel.'))
            
            if rec.document_ownership_handover_id.state == 'cancel':
                raise ValidationError(_('This ownership document handover is already cancelled.'))

    def action_confirm(self):
        self._validity_check()
        for rec in self:
            rec.document_ownership_handover_id.ownership_handover_line_ids.action_cancel()
            rec.document_ownership_handover_id.action_cancel()
        return self.cancellation_id.action_confirm()

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete a cancellation that is not in draft status."))

    def action_request_approval(self):
        return super().action_request_approval(value=5)

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)