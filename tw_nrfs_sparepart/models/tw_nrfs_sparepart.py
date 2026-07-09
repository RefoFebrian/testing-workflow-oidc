# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
import odoo.addons.base.models.decimal_precision as dp

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritTWNrfsSparepart(models.Model):
    _inherit = "tw.nrfs"
    
    # 7: defaults methods

    # 8: fields
    claim_to = fields.Selection([
        ('AHM','AHM'),
        ('Expedisi','Expedisi')
    ], string='Claim To', help='Claim to AHM or Expedition')
    claim_type = fields.Selection([
        ('item','Item Replaced'),
        ('money','Money Replaced'),
        ('disposal','Disposal'),
    ], string='Claim Type')

    # Audit Trail 
    validate_uid = fields.Many2one('res.users', string='Validate by')
    validate_date = fields.Datetime(string='Validate on')

    # 9: relation fields
    partner_id = fields.Many2one('res.partner', string='Partner')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('claim_to')
    def _onchange_claim_to(self):
        self.claim_type = False
        if self.claim_to == 'Expedisi':
            self.claim_type = 'money'

    @api.onchange('claim_type')
    def _onchange_claim_type(self):
        self.partner_id = False

    # 12: override methods

    # 13: action methods
    def action_confirm(self):
        if self.division == 'Sparepart':
            for record in self.line_ids:
                if not record.annotation:
                    raise Warning("Please fill in 'Keterangan Rusak'!")
        return super(InheritTWNrfsSparepart,self).action_confirm()
    
    def action_cancel(self):
        return super(InheritTWNrfsSparepart,self).action_cancel()
        
    def action_validate(self):
        self.suspend_security().write({
            'state':'done',
            'validate_uid':self.env.user.id,
            'validate_date':datetime.now()
        })

    # 14: private methods

