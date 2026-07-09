# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError as Warning
from markupsafe import Markup


class tw_petty_cash_in_approval(models.Model):
    _name = "tw.reimbursement.petty.cash"
    _inherit = ["tw.reimbursement.petty.cash","tw.approval.mixin"]
    state = fields.Selection(selection_add=[
        ('draft',),
        ('confirmed','Confirmed'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('paid',),
        ('cancel',),
    ], string="Status",ondelete={
            'draft': 'set default',
            'confirmed': 'set default',
            'waiting_for_approval': 'set default',
            'approved': 'set default',
            'paid': 'set default',
            'cancel': 'set default',
        })

    def action_request_approval(self):
        for rec in self:
            pco_names = '<br>'.join(rec.petty_cash_out_ids.mapped('name'))
            rec.message_post(
                body=Markup(f"Reimbursement <b>{rec.name or '(tanpa nama)'}</b> diajukan untuk approval.<br> Petty Cash No: <br>{pco_names}"),
                subtype_xmlid="mail.mt_note"
            )
        self.petty_cash_out_ids.write({
            'reimbursed_id': self.id,
        })
        return super().action_request_approval()

    def action_approval(self):
        for rec in self:
            pco_names = '<br>'.join(rec.petty_cash_out_ids.mapped('name'))
            rec.message_post(
                body=Markup(f"Reimbursement <b>{rec.name or '(tanpa nama)'}</b> Approved.<br> Petty Cash No: <br>{pco_names}"),
                subtype_xmlid="mail.mt_note"
            )
        return super().action_approval()

    def get_approve_additional_vals(self):
        self.ensure_one()
        self.petty_cash_out_ids.write({
            'state': 'reimbursed',
        })
        return {
            'confirm_uid': self._uid,
            'confirm_date': datetime.now(),
            'state': 'approved'
        }

    def validate_order(self):
        for rec in self:
            if not rec.petty_cash_out_ids:
                raise ValidationError('Please input petty cash out.')
            for petty_cash_out_id in rec.petty_cash_out_ids:
                if petty_cash_out_id.reimbursed_id and petty_cash_out_id.reimbursed_id.id != rec.id:
                    raise ValidationError(f'Petty cash out {petty_cash_out_id.name} have been reimbursed in {petty_cash_out_id.reimbursed_id.name}.')
