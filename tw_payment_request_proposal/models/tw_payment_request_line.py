# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritAccountPaymentRequestLine(models.Model):
    _inherit = "tw.payment.request.line"

    # 8: fields
    proposal_line_id = fields.Many2one('tw.proposal.line', string='Item Proposal', ondelete='restrict')


    @api.onchange('proposal_line_id')
    def _onchange_name_and_amount(self):
        self.name = False
        self.amount = 0
        if self.proposal_line_id:
            self.name = self.proposal_line_id.description
            self.amount = self.proposal_line_id.amount_total - (self.proposal_line_id.amount_reserved + self.proposal_line_id.amount_paid)
            if self.amount <= 0:
                raise Warning('Item Proposal %s sudah dibayar sepenuhnya.' % self.proposal_line_id.description)
