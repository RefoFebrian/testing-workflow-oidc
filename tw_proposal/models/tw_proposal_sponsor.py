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

class TWProposalSponsor(models.Model):
    _name = "tw.proposal.sponsor"
    _description = "Proposal Online - Sponsor"


    # 7: defaults methods
    
    # 8: fields
    amount = fields.Float(string='Nominal', digits='Product Price')
    
    # 9: relation fields
    proposal_id = fields.Many2one('tw.proposal', string='Nomor Proposal', ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', string='Sponsor', ondelete='restrict')

    @api.constrains('amount')
    def _check_amount(self):
        if self.amount <= 0:
            raise Warning('Beban sponsor %s harus lebih dari 0.' % (self.supplier_id.name))