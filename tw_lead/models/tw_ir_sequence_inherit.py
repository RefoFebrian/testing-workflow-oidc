# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, SUPERUSER_ID, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class IrSequence(models.Model):
    _inherit = "ir.sequence"


    def get_lead_partner_sequence(self, branch_code, code_name_prospek):
        seq_name = f'PRS/{branch_code}'
        ids = self.search([('name', '=', seq_name)])
        seq_name_bk = f'H2Z/{branch_code}'
        if not ids:
            prefix = '/%(y)s/%(month)s/PSP/'+ code_name_prospek+'/'
            prefix = seq_name_bk + prefix 
            ids = self.env['ir.sequence'].create({
                'name':seq_name,
                'implementation': 'standard',
                'prefix': prefix,
                'padding':5
            })
        return ids.next_by_id()
    
    def get_code_transaksi_4(self, code, prefix):
        seq_name = '{0}/{1}'.format(code,prefix)
        ids = self.search([('name', '=', seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            vals = {
                'name':seq_name,
                'implementation':'no_gap',
                'prefix':prefix,
                'padding':4
            }
            ids = self.create(vals)
        return ids.next_by_id()