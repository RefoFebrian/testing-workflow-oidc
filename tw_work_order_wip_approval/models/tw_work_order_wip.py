# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning


# 5: local imports

# 6: Import of unknown third party lib

class InheritTwWorkOrderWip(models.Model):
    _name = "tw.work.order.wip"
    _inherit = ['tw.work.order.wip','tw.approval.mixin']

    # 7: defaults methods

    # 8: fields

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('done',),
    ], string="Status")

    # 9: relation fields
    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _inherit)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_rfa(self):
        self.ensure_one()
        for line in self.detail_ids:
            if not line.motorbike_physics or not line.description:
                raise Warning("Harap lengkapi bagian 'Fisik Motor' dan 'Keterangan' sebelum melanjutkan ke RFA.")

        for line in self.detail_ids:
            line.validation_status = 'open'
        for other in self.other_ids:
            other.validation_status = 'open'
        
        # TODO: Confirmasi untuk Valuenya mau berapa?, di TEDS Exisiting gak ada matrix soalnya
        return super().action_request_approval(value=2)

    def action_approval(self):
        for line in self.detail_ids:
            if not line.is_validasi_adh:
                raise Warning("Harap ceklis 'Validasi ADH' sebelum Approve")
        for line in self.detail_ids:
            line.validation_status = 'done'
        for other in self.other_ids:
            other.validation_status = 'done'

        return super().action_approval()

    def action_reject(self):
        self._back_to_draft_line()
        return super().action_reject_or_cancel(update_values={'state': 'draft'})

    def action_cancel_approval(self):
        self._back_to_draft_line()
        return super().action_reject_or_cancel(update_values={'state': 'draft'})

    # 14: private methods
    def _back_to_draft_line(self):
        for detail in self.detail_ids:
            detail.write({'validation_status': 'draft', 'is_validasi_adh': False})
        for other in self.other_ids:
            other.write({'validation_status': 'draft', 'is_validasi_adh': False})