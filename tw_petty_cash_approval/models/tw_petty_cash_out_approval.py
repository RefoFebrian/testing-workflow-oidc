# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime 
from odoo.exceptions import ValidationError, UserError as Warning
from markupsafe import Markup

class tw_petty_cash_out_approval(models.Model):
    _name = "tw.petty.cash.out"
    _inherit = ["tw.petty.cash.out","tw.approval.mixin"]
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

    def action_request_approval(self):
        for rec in self:
            rec.validate_order()
            pco_line_names = '<br>'.join(rec.petty_cash_out_line_ids.mapped('name'))
            rec.sudo().message_post(
                body=Markup(f"Petty Cash Out <b>{rec.name or '(tanpa nama)'}</b> diajukan untuk approval.<br> Petty Cash Line: <br>{pco_line_names}"),
                subtype_xmlid="mail.mt_note"
            )
        amount_total = self.get_total_value()
        return super().action_request_approval(value=amount_total)
    
    def action_approval(self):
        for rec in self:
            pco_line_names = '<br>'.join(rec.petty_cash_out_line_ids.mapped('name'))
            rec.sudo().message_post(
                body=Markup(f"Petty Cash Out <b>{rec.name or '(tanpa nama)'}</b> Approved.<br> Petty Cash Line: <br>{pco_line_names}"),
                subtype_xmlid="mail.mt_note"
            )
        return super().action_approval()

    def _get_to_post(self):
        return self.filtered(lambda r: r.state == 'approved')

