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


    @api.model
    def next_by_month_and_code(self, sequence_code, sequence_date=None):
        """ Draw an interpolated string using a sequence with the requested code.
            If several sequences with the correct code are available to the user
            (multi-company cases), the one from the user's current company will
            be used.
        """
        self.browse().check_access('read')
        company_id = self.env.company.id
        seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [company_id, False])], order='company_id')
        if not seq_ids:
            return False
        seq_id = seq_ids[0]
        return seq_id._next(sequence_date=sequence_date)
    


    def get_sequence(self, cr, uid, first_prefix, context=None):
        ids = self.search(cr, uid, [('name','=',first_prefix)])
        if not ids:
            prefix = first_prefix + '/%(y)s/%(month)s/'
            ids = self.create(cr, SUPERUSER_ID, {'name': first_prefix,
                                 'implementation': 'standard',
                                 'prefix': prefix,
                                 'padding': 5})
            
        return self.get_id(cr, uid, ids, context={'tz':'Asia/Jakarta'})
    