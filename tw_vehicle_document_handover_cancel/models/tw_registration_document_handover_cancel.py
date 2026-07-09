# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class TwRegistrationDocumentHandoverCancel(models.Model):
    _name = "tw.registration.document.handover.cancel"
    _description = 'Penyerahan STNK Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'

    def _get_default_date(self):
        return fields.Date.today()

    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    document_registration_handover_id = fields.Many2one(
        'tw.vehicle.registration.handover',
        string='Penyerahan STNK',
        required=True,
    )
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.document_registration_handover_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('document_registration_handover_id'):
                document_registration_handover_id = self.env['tw.vehicle.registration.handover'].browse(vals['document_registration_handover_id'])
                vals['transaction_name'] = document_registration_handover_id.name
                name = "X" + document_registration_handover_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + document_registration_handover_id.name
                vals['date'] = self._get_default_date()
        return super().create(vals_list)

    # Constraint Methods
    def _validity_check(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            if not rec.document_registration_handover_id:
                raise ValidationError(_('Please select a document handover to cancel.'))
            
            # Check if handover is already cancelled
            if rec.document_registration_handover_id.state == 'cancel':
                raise ValidationError(_('This document handover is already cancelled.'))

    def action_confirm(self):
        self._validity_check()
        for rec in self:
            # Cancel all lines in the handover
            rec.document_registration_handover_id.registration_handover_line_ids.action_cancel()
            
            # Cancel the handover itself
            rec.document_registration_handover_id.action_cancel()
        
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