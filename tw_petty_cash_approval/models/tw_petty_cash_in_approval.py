# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime 
from odoo.exceptions import ValidationError, UserError as Warning
from markupsafe import Markup

class tw_petty_cash_in_approval(models.Model):
    _name = "tw.petty.cash.in"
    _inherit = ["tw.petty.cash.in","tw.approval.mixin"]
    state = fields.Selection(selection_add=[
        ('draft',),
        ('confirmed','Confirmed'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('posted',),
        ('cancel',),
    ], string="Status",ondelete={
            'draft': 'set default',
            'confirmed': 'set default',
            'waiting_for_approval': 'set default',
            'approved': 'set default',
            'posted': 'set default',
            'cancel': 'set default',
        })

    def action_post_petty_cash_in(self):
        for rec in self.filtered(lambda r: r.state == 'approved'):
            rec.validate_order()
            rec.write({
                'period_id': self._get_period(),
                'date': fields.Date.today(),
                'state': 'posted',
                'confirm_uid': self.env.uid,
                'confirm_date': datetime.now()
            })
            rec.sudo()._action_move_line_in_create()
            if rec._is_inter_company():
                rec.sudo()._action_aml_inter_company_create()
            rec.move_id.sudo().action_post()
            rec.petty_cash_out_id.sudo().action_recalculate_amount_real()

            pci_line_names = '<br>'.join(rec.petty_cash_in_line_ids.mapped('name'))
            rec.message_post(
                body=Markup(f"Petty Cash In <b>{rec.name or '(tanpa nama)'}</b> Posted.<br> Petty Cash Line: <br>{pci_line_names}"),
                subtype_xmlid="mail.mt_note"
            )

    def action_request_approval(self):
        pci_line_names = '<br>'.join(self.petty_cash_in_line_ids.mapped('name'))
        self.message_post(
            body=Markup(f"Petty Cash In <b>{self.name or '(tanpa nama)'}</b> diajukan untuk approval.<br> Petty Cash Line: <br>{pci_line_names}"),
            subtype_xmlid="mail.mt_note"
        )

        amount_total = self.get_total_value()
        return super().action_request_approval(value=amount_total)

    def action_approval(self):
        for rec in self:
            pci_line_names = '<br>'.join(rec.petty_cash_in_line_ids.mapped('name'))
            rec.message_post(
                body=Markup(f"Petty Cash In <b>{rec.name or '(tanpa nama)'}</b> Approved.<br> Petty Cash Line: <br>{pci_line_names}"),
                subtype_xmlid="mail.mt_note"
            )
        return super().action_approval()

    def get_approve_additional_vals(self):
        self.ensure_one()
        return {
            'confirm_uid': self._uid,
            'confirm_date': datetime.now(),
            'state': 'approved'
        }
