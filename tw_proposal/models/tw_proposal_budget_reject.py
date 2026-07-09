# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TwProposalRejectBudget(models.TransientModel):
    _name = "tw.proposal.budget.reject"
    _description = "Proposal Online - Reject Budget"
    
    proposal_id = fields.Many2one('tw.proposal', string='ID Proposal', ondelete='cascade')
    reject_reason = fields.Text(string='Alasan Reject')

    def action_reject(self):
        if self.env['tw.approval.matrixbiaya'].suspend_security().reject(self.proposal_id, self.reject_reason):
            try:
                self.proposal_id.suspend_security().write({'state': 'reject','approval_state':'r'})
            except Exception:
                self._cr.rollback()
                raise Warning('Terjadi kesalahan saat update Proposal %s.' % (self.proposal_id.suspend_security().name))
        else:
            raise Warning("User tidak termasuk group approval.")
        return True
